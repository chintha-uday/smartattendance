import os
from datetime import date, datetime, time, timedelta

from app.database import Base, SessionLocal, engine
from app.models import Attendance, AttendanceSession, Department, Employee, Role, Shift, User
from app.security import hash_password

DEMO_EMPLOYEES = [
    ("DEMO001", "Avery Rao", "demo.avery", [(8, 58), (9, 24), (9, 5), (8, 52), (9, 2)]),
    ("DEMO002", "Sam Rivera", "demo.sam", [(9, 8), (9, 4), (9, 1), (9, 12), (9, 6)]),
    ("DEMO003", "Jordan Lee", "demo.jordan", [(8, 55), (9, 18), (9, 25), (9, 0), (8, 59)]),
]
DEMO_PASSWORD = "DemoPass2026!"


def previous_workdays(count: int) -> list[date]:
    days = []
    current = date.today() - timedelta(days=1)
    while len(days) < count:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))


def seed_demo_data() -> None:
    if os.getenv("APP_DEMO_DATA") != "1":
        raise RuntimeError("Demo seeding requires APP_DEMO_DATA=1.")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo_codes = [item[0] for item in DEMO_EMPLOYEES]
        existing_demo_count = db.query(Employee).filter(Employee.code.in_(demo_codes)).count()
        if existing_demo_count == len(DEMO_EMPLOYEES):
            return
        if db.query(Employee).count() or db.query(Attendance).count():
            raise RuntimeError("Refusing to add demo records to a non-empty database.")

        for name in ["Admin", "HR", "Manager", "Employee"]:
            if not db.query(Role).filter_by(name=name).first():
                db.add(Role(name=name))
        if not db.query(Department).first():
            db.add(Department(name="General"))
        if not db.query(Shift).first():
            db.add(Shift(name="General", start_time=time(9, 0), end_time=time(18, 0),
                         grace_minutes=10, break_minutes=60))
        db.flush()

        employee_role = db.query(Role).filter_by(name="Employee").one()
        department = db.query(Department).filter_by(is_active=True).first()
        shift = db.query(Shift).filter_by(is_active=True).first()
        workdays = previous_workdays(5)
        checkout_times = [(17, 45), (18, 0), (17, 45), (18, 0), (17, 45)]
        password_hash = hash_password(DEMO_PASSWORD)

        for code, full_name, username, checkin_times in DEMO_EMPLOYEES:
            employee = Employee(code=code, full_name=full_name, department_id=department.id,
                                shift_id=shift.id, joining_date=workdays[0])
            db.add(employee)
            db.flush()
            db.add(User(employee_id=employee.id, role_id=employee_role.id, username=username,
                        password_hash=password_hash))

            for index, workday in enumerate(workdays):
                check_in = datetime.combine(workday, time(*checkin_times[index]))
                if code == "DEMO002" and index == 2:
                    check_out = datetime.combine(workday, time(13, 15))
                    status = "HalfDay"
                else:
                    check_out = datetime.combine(workday, time(*checkout_times[index]))
                    late_after = datetime.combine(workday, shift.start_time) + timedelta(
                        minutes=shift.grace_minutes
                    )
                    status = "Late" if check_in > late_after else "Present"

                late_after = datetime.combine(workday, shift.start_time) + timedelta(
                    minutes=shift.grace_minutes
                )
                shift_end = datetime.combine(workday, shift.end_time)
                attendance = Attendance(
                    employee_id=employee.id,
                    attendance_date=workday,
                    status=status,
                    work_minutes=max(
                        0, int((check_out - check_in).total_seconds() // 60) - shift.break_minutes
                    ),
                    late_minutes=max(0, int((check_in - late_after).total_seconds() // 60)),
                    early_departure_minutes=max(
                        0, int((shift_end - check_out).total_seconds() // 60)
                    ),
                )
                db.add(attendance)
                db.flush()
                db.add(AttendanceSession(attendance_id=attendance.id,
                                         check_in_time=check_in, check_out_time=check_out))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
