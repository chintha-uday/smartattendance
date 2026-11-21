from datetime import datetime, date, time, timedelta
from io import BytesIO, StringIO
import csv
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.config import settings
from app.database import Base, engine, get_db, SessionLocal
from app import models
from app.models import User, Role, Employee, Department, Shift, Attendance, AttendanceSession, LeaveRequest, Holiday
from app.security import hash_password, verify_password, current_user, require_user, require_roles
from app.audit import log_action

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=settings.APP_SECRET_KEY,
                   same_site="lax", https_only=(settings.APP_ENV == "production"))
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for name in ["Admin", "HR", "Manager", "Employee"]:
            if not db.query(Role).filter_by(name=name).first():
                db.add(Role(name=name))
        if not db.query(Department).first():
            db.add(Department(name="General"))
        if not db.query(Shift).first():
            db.add(Shift(name="General", start_time=time(9,0), end_time=time(18,0),
                         grace_minutes=10, break_minutes=60))
        db.commit()
    finally:
        db.close()

def page(request, db, template, **context):
    user = current_user(request, db)
    return templates.TemplateResponse(template, {"request": request, "user": user, **context})

def today_local():
    # Office deployment defaults to India local server time.
    return datetime.now().date()

def employee_for(user, db):
    if not user.employee_id:
        raise HTTPException(400, "This account is not linked to an employee")
    emp = db.query(Employee).filter_by(id=user.employee_id, is_active=True).first()
    if not emp:
        raise HTTPException(403, "Employee account is inactive")
    return emp

@app.get("/health")
def health():
    return {"status": "ok", "application": settings.APP_NAME}

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/dashboard", status_code=303)
    return page(request, db, "login.html", error=None)

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.role)).filter(
        func.lower(User.username) == username.lower().strip(), User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        return page(request, db, "login.html", error="Invalid username or password")
    request.session.clear()
    request.session["user_id"] = user.id
    log_action(db, user.id, "LOGIN", "Users", user.id)
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@app.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if uid:
        log_action(db, uid, "LOGOUT", "Users", uid)
        db.commit()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    today = today_local()
    if user.role.name == "Employee":
        emp = employee_for(user, db)
        att = db.query(Attendance).filter_by(employee_id=emp.id, attendance_date=today).first()
        sess = db.query(AttendanceSession).filter_by(attendance_id=att.id).order_by(AttendanceSession.id.desc()).first() if att else None
        return page(request, db, "employee_dashboard.html", attendance=att, session=sess, today=today)
    active = db.query(Employee).filter_by(is_active=True).count()
    present = db.query(Attendance).filter(Attendance.attendance_date == today, Attendance.status.in_(["Present","Late","Incomplete"])).count()
    late = db.query(Attendance).filter_by(attendance_date=today, status="Late").count()
    on_leave = db.query(LeaveRequest).filter(LeaveRequest.status=="Approved",
        LeaveRequest.from_date <= today, LeaveRequest.to_date >= today).count()
    rows = db.query(Attendance).options(joinedload(Attendance.employee)).filter_by(attendance_date=today).all()
    return page(request, db, "admin_dashboard.html", today=today, active=active,
                present=present, absent=max(active-present-on_leave,0), late=late,
                on_leave=on_leave, rows=rows)

@app.post("/attendance/check-in")
def check_in(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    emp = employee_for(user, db)
    now = datetime.now()
    today = now.date()
    att = db.query(Attendance).filter_by(employee_id=emp.id, attendance_date=today).with_for_update().first()
    if not att:
        att = Attendance(employee_id=emp.id, attendance_date=today, status="Pending")
        db.add(att); db.flush()
    open_session = db.query(AttendanceSession).filter_by(attendance_id=att.id, check_out_time=None).first()
    if open_session:
        raise HTTPException(409, "You are already checked in.")
    if db.query(AttendanceSession).filter_by(attendance_id=att.id).first():
        raise HTTPException(409, "A check-in is already recorded for today.")
    shift = emp.shift
    shift_start = datetime.combine(today, shift.start_time)
    late_after = shift_start + timedelta(minutes=shift.grace_minutes)
    late_minutes = max(0, int((now-late_after).total_seconds()//60))
    att.late_minutes = late_minutes
    att.status = "Late" if late_minutes > 0 else "Present"
    db.add(AttendanceSession(attendance_id=att.id, check_in_time=now))
    log_action(db, user.id, "CHECK_IN", "Attendance", att.id, new_value=now.isoformat())
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@app.post("/attendance/check-out")
def check_out(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    emp = employee_for(user, db)
    today = today_local()
    att = db.query(Attendance).filter_by(employee_id=emp.id, attendance_date=today).first()
    if not att:
        raise HTTPException(400, "No check-in found for today.")
    sess = db.query(AttendanceSession).filter_by(attendance_id=att.id, check_out_time=None).first()
    if not sess:
        raise HTTPException(400, "No open check-in session found.")
    now = datetime.now()
    if now <= sess.check_in_time:
        raise HTTPException(400, "Check-out must be after check-in.")
    sess.check_out_time = now
    shift_end = datetime.combine(today, emp.shift.end_time)
    att.early_departure_minutes = max(0, int((shift_end-now).total_seconds()//60))
    gross = int((now-sess.check_in_time).total_seconds()//60)
    att.work_minutes = max(0, gross - emp.shift.break_minutes)
    if att.work_minutes < 240:
        att.status = "HalfDay"
    elif att.status == "Pending":
        att.status = "Present"
    att.updated_at = datetime.utcnow()
    log_action(db, user.id, "CHECK_OUT", "Attendance", att.id, new_value=now.isoformat())
    db.commit()
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/employees")
def employees_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR")
    rows = db.query(Employee).options(joinedload(Employee.department), joinedload(Employee.shift)).order_by(Employee.code).all()
    depts = db.query(Department).filter_by(is_active=True).all()
    shifts = db.query(Shift).filter_by(is_active=True).all()
    return page(request, db, "employees.html", rows=rows, departments=depts, shifts=shifts, error=None)

@app.post("/employees")
def create_employee(request: Request, code: str = Form(...), full_name: str = Form(...),
                    username: str = Form(...), password: str = Form(...),
                    department_id: int = Form(...), shift_id: int = Form(...),
                    email: str = Form(""), db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR")
    if db.query(Employee).filter_by(code=code.strip()).first() or db.query(User).filter_by(username=username.strip()).first():
        raise HTTPException(409, "Employee code or username already exists")
    role = db.query(Role).filter_by(name="Employee").one()
    emp = Employee(code=code.strip(), full_name=full_name.strip(), email=email.strip() or None,
                   department_id=department_id, shift_id=shift_id, joining_date=today_local())
    db.add(emp); db.flush()
    db.add(User(employee_id=emp.id, role_id=role.id, username=username.strip(),
                password_hash=hash_password(password)))
    log_action(db, user.id, "CREATE_EMPLOYEE", "Employees", emp.id)
    db.commit()
    return RedirectResponse("/employees", status_code=303)

@app.post("/employees/{employee_id}/deactivate")
def deactivate_employee(employee_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR")
    emp = db.query(Employee).filter_by(id=employee_id).first()
    if emp:
        emp.is_active = False
        account = db.query(User).filter_by(employee_id=emp.id).first()
        if account: account.is_active = False
        log_action(db, user.id, "DEACTIVATE_EMPLOYEE", "Employees", emp.id)
        db.commit()
    return RedirectResponse("/employees", status_code=303)

@app.get("/attendance")
def attendance_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role.name == "Employee":
        emp = employee_for(user, db)
        rows = db.query(Attendance).filter_by(employee_id=emp.id).order_by(Attendance.attendance_date.desc()).limit(60).all()
    else:
        rows = db.query(Attendance).options(joinedload(Attendance.employee)).order_by(Attendance.attendance_date.desc()).limit(250).all()
    return page(request, db, "attendance.html", rows=rows)

@app.get("/shifts")
def shifts_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR")
    rows = db.query(Shift).all()
    return page(request, db, "shifts.html", rows=rows)

@app.post("/shifts")
def create_shift(request: Request, name: str = Form(...), start_time: str = Form(...),
                 end_time: str = Form(...), grace_minutes: int = Form(10),
                 db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR")
    db.add(Shift(name=name.strip(), start_time=time.fromisoformat(start_time),
                 end_time=time.fromisoformat(end_time), grace_minutes=grace_minutes))
    log_action(db, user.id, "CREATE_SHIFT", "Shifts", new_value=name)
    db.commit()
    return RedirectResponse("/shifts", status_code=303)

@app.get("/leaves")
def leaves_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    if user.role.name == "Employee":
        emp = employee_for(user, db)
        rows = db.query(LeaveRequest).filter_by(employee_id=emp.id).order_by(LeaveRequest.created_at.desc()).all()
    else:
        rows = db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()
    return page(request, db, "leaves.html", rows=rows)

@app.post("/leaves")
def apply_leave(request: Request, from_date: str = Form(...), to_date: str = Form(...),
                leave_type: str = Form("Casual"), reason: str = Form(""),
                db: Session = Depends(get_db)):
    user = require_user(request, db)
    emp = employee_for(user, db)
    start, end = date.fromisoformat(from_date), date.fromisoformat(to_date)
    if end < start: raise HTTPException(400, "End date must be on or after start date")
    db.add(LeaveRequest(employee_id=emp.id, from_date=start, to_date=end,
                        leave_type=leave_type, reason=reason))
    log_action(db, user.id, "APPLY_LEAVE", "LeaveRequests")
    db.commit()
    return RedirectResponse("/leaves", status_code=303)

@app.post("/leaves/{leave_id}/decision")
def leave_decision(leave_id: int, request: Request, decision: str = Form(...),
                   db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR", "Manager")
    item = db.query(LeaveRequest).filter_by(id=leave_id).first()
    if item and decision in ["Approved", "Rejected"]:
        item.status = decision; item.approved_by = user.id
        log_action(db, user.id, "LEAVE_"+decision.upper(), "LeaveRequests", item.id)
        db.commit()
    return RedirectResponse("/leaves", status_code=303)

@app.get("/reports.csv")
def reports_csv(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR", "Manager")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee Code","Employee Name","Date","Status","Check In","Check Out","Work Minutes","Late Minutes"])
    query = db.query(Attendance).options(joinedload(Attendance.employee))
    if user.role.name == "Manager" and user.employee_id:
        query = query.filter(Attendance.employee_id == user.employee_id)
    for att in query.order_by(Attendance.attendance_date.desc()).all():
        sessions = db.query(AttendanceSession).filter_by(attendance_id=att.id).order_by(AttendanceSession.id).all()
        first = sessions[0] if sessions else None
        writer.writerow([att.employee.code, att.employee.full_name, att.attendance_date,
                         att.status, first.check_in_time if first else "",
                         first.check_out_time if first else "", att.work_minutes or "",
                         att.late_minutes])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition":"attachment; filename=attendance-report.csv"})

@app.get("/admin/attendance")
def admin_attendance(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db); require_roles(user, "Admin", "HR")
    rows = db.query(Attendance).options(joinedload(Attendance.employee)).order_by(Attendance.attendance_date.desc()).limit(500).all()
    return page(request, db, "attendance.html", rows=rows)

@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    return HTMLResponse(f"<h2>Request could not be completed</h2><p>{exc.detail}</p><p><a href='/dashboard'>Return to dashboard</a></p>", status_code=exc.status_code)
