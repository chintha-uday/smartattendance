from datetime import datetime, date, time
from sqlalchemy import (String, Integer, Boolean, Date, DateTime, Time, ForeignKey,
                        UniqueConstraint, CheckConstraint, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Role(Base):
    __tablename__ = "Roles"
    id: Mapped[int] = mapped_column("RoleId", Integer, primary_key=True)
    name: Mapped[str] = mapped_column("RoleName", String(30), unique=True, nullable=False)

class Department(Base):
    __tablename__ = "Departments"
    id: Mapped[int] = mapped_column("DepartmentId", Integer, primary_key=True)
    name: Mapped[str] = mapped_column("DepartmentName", String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True)

class Shift(Base):
    __tablename__ = "Shifts"
    id: Mapped[int] = mapped_column("ShiftId", Integer, primary_key=True)
    name: Mapped[str] = mapped_column("ShiftName", String(100), nullable=False)
    start_time: Mapped[time] = mapped_column("StartTime", Time, default=time(9,0))
    end_time: Mapped[time] = mapped_column("EndTime", Time, default=time(18,0))
    grace_minutes: Mapped[int] = mapped_column("GraceMinutes", Integer, default=10)
    break_minutes: Mapped[int] = mapped_column("BreakMinutes", Integer, default=60)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True)

class Employee(Base):
    __tablename__ = "Employees"
    id: Mapped[int] = mapped_column("EmployeeId", Integer, primary_key=True)
    code: Mapped[str] = mapped_column("EmployeeCode", String(30), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column("FullName", String(150), nullable=False)
    email: Mapped[str | None] = mapped_column("Email", String(150))
    department_id: Mapped[int | None] = mapped_column("DepartmentId", ForeignKey("Departments.DepartmentId"))
    shift_id: Mapped[int] = mapped_column("ShiftId", ForeignKey("Shifts.ShiftId"))
    joining_date: Mapped[date] = mapped_column("JoiningDate", Date, default=date.today)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=datetime.utcnow)
    department = relationship("Department")
    shift = relationship("Shift")

class User(Base):
    __tablename__ = "Users"
    id: Mapped[int] = mapped_column("UserId", Integer, primary_key=True)
    employee_id: Mapped[int | None] = mapped_column("EmployeeId", ForeignKey("Employees.EmployeeId"), unique=True)
    role_id: Mapped[int] = mapped_column("RoleId", ForeignKey("Roles.RoleId"))
    username: Mapped[str] = mapped_column("Username", String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column("PasswordHash", String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=datetime.utcnow)
    role = relationship("Role")
    employee = relationship("Employee")

class Attendance(Base):
    __tablename__ = "Attendance"
    __table_args__ = (UniqueConstraint("EmployeeId", "AttendanceDate", name="UQ_Attendance_Employee_Date"),)
    id: Mapped[int] = mapped_column("AttendanceId", Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column("EmployeeId", ForeignKey("Employees.EmployeeId"), nullable=False)
    attendance_date: Mapped[date] = mapped_column("AttendanceDate", Date, nullable=False)
    status: Mapped[str] = mapped_column("Status", String(20), default="Pending")
    work_minutes: Mapped[int | None] = mapped_column("WorkMinutes", Integer)
    late_minutes: Mapped[int] = mapped_column("LateMinutes", Integer, default=0)
    early_departure_minutes: Mapped[int] = mapped_column("EarlyDepartureMinutes", Integer, default=0)
    remarks: Mapped[str | None] = mapped_column("Remarks", String(500))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    employee = relationship("Employee")

class AttendanceSession(Base):
    __tablename__ = "AttendanceSessions"
    __table_args__ = (
        CheckConstraint(
            '"CheckOutTime" IS NULL OR "CheckOutTime" > "CheckInTime"',
            name="CK_Session_Time",
        ),
    )
    id: Mapped[int] = mapped_column("SessionId", Integer, primary_key=True)
    attendance_id: Mapped[int] = mapped_column("AttendanceId", ForeignKey("Attendance.AttendanceId"), nullable=False)
    check_in_time: Mapped[datetime] = mapped_column("CheckInTime", DateTime, nullable=False)
    check_out_time: Mapped[datetime | None] = mapped_column("CheckOutTime", DateTime)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=datetime.utcnow)
    attendance = relationship("Attendance")

class LeaveRequest(Base):
    __tablename__ = "LeaveRequests"
    id: Mapped[int] = mapped_column("LeaveRequestId", Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column("EmployeeId", ForeignKey("Employees.EmployeeId"))
    from_date: Mapped[date] = mapped_column("FromDate", Date)
    to_date: Mapped[date] = mapped_column("ToDate", Date)
    leave_type: Mapped[str] = mapped_column("LeaveType", String(30))
    reason: Mapped[str | None] = mapped_column("Reason", String(500))
    status: Mapped[str] = mapped_column("Status", String(20), default="Pending")
    approved_by: Mapped[int | None] = mapped_column("ApprovedBy", ForeignKey("Users.UserId"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=datetime.utcnow)

class Holiday(Base):
    __tablename__ = "Holidays"
    id: Mapped[int] = mapped_column("HolidayId", Integer, primary_key=True)
    holiday_date: Mapped[date] = mapped_column("HolidayDate", Date, nullable=False, unique=True)
    name: Mapped[str] = mapped_column("HolidayName", String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column("IsActive", Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "AuditLogs"
    id: Mapped[int] = mapped_column("AuditId", Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column("UserId", ForeignKey("Users.UserId"))
    action: Mapped[str] = mapped_column("Action", String(100), nullable=False)
    table_name: Mapped[str | None] = mapped_column("TableName", String(100))
    record_id: Mapped[str | None] = mapped_column("RecordId", String(100))
    old_value: Mapped[str | None] = mapped_column("OldValue", Text)
    new_value: Mapped[str | None] = mapped_column("NewValue", Text)
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime, default=datetime.utcnow)

class SystemSetting(Base):
    __tablename__ = "SystemSettings"
    key: Mapped[str] = mapped_column("SettingKey", String(100), primary_key=True)
    value: Mapped[str] = mapped_column("SettingValue", String(500), nullable=False)
