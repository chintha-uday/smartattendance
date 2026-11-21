-- SmartAttendanceDB SQL Server schema
-- Run using a SQL Server account permitted to create databases.
IF DB_ID(N'SmartAttendanceDB') IS NULL
    CREATE DATABASE SmartAttendanceDB;
GO
USE SmartAttendanceDB;
GO
CREATE TABLE Roles (
 RoleId INT IDENTITY(1,1) PRIMARY KEY,
 RoleName VARCHAR(30) NOT NULL UNIQUE
);
CREATE TABLE Departments (
 DepartmentId INT IDENTITY(1,1) PRIMARY KEY,
 DepartmentName VARCHAR(100) NOT NULL UNIQUE,
 IsActive BIT NOT NULL DEFAULT 1
);
CREATE TABLE Shifts (
 ShiftId INT IDENTITY(1,1) PRIMARY KEY,
 ShiftName VARCHAR(100) NOT NULL,
 StartTime TIME NOT NULL,
 EndTime TIME NOT NULL,
 GraceMinutes INT NOT NULL DEFAULT 10,
 BreakMinutes INT NOT NULL DEFAULT 60,
 IsActive BIT NOT NULL DEFAULT 1
);
CREATE TABLE Employees (
 EmployeeId INT IDENTITY(1,1) PRIMARY KEY,
 EmployeeCode VARCHAR(30) NOT NULL UNIQUE,
 FullName VARCHAR(150) NOT NULL,
 Email VARCHAR(150) NULL,
 DepartmentId INT NULL REFERENCES Departments(DepartmentId),
 ShiftId INT NOT NULL REFERENCES Shifts(ShiftId),
 JoiningDate DATE NOT NULL,
 IsActive BIT NOT NULL DEFAULT 1,
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE Users (
 UserId INT IDENTITY(1,1) PRIMARY KEY,
 EmployeeId INT NULL UNIQUE REFERENCES Employees(EmployeeId),
 RoleId INT NOT NULL REFERENCES Roles(RoleId),
 Username VARCHAR(100) NOT NULL UNIQUE,
 PasswordHash VARCHAR(255) NOT NULL,
 IsActive BIT NOT NULL DEFAULT 1,
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE Attendance (
 AttendanceId BIGINT IDENTITY(1,1) PRIMARY KEY,
 EmployeeId INT NOT NULL REFERENCES Employees(EmployeeId),
 AttendanceDate DATE NOT NULL,
 Status VARCHAR(20) NOT NULL DEFAULT 'Pending',
 WorkMinutes INT NULL,
 LateMinutes INT NOT NULL DEFAULT 0,
 EarlyDepartureMinutes INT NOT NULL DEFAULT 0,
 Remarks VARCHAR(500) NULL,
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
 UpdatedAt DATETIME2 NULL,
 CONSTRAINT UQ_Attendance_Employee_Date UNIQUE(EmployeeId, AttendanceDate),
 CONSTRAINT CK_Attendance_Status CHECK(Status IN
 ('Pending','Present','Late','HalfDay','Absent','Leave','Holiday','Incomplete'))
);
CREATE TABLE AttendanceSessions (
 SessionId BIGINT IDENTITY(1,1) PRIMARY KEY,
 AttendanceId BIGINT NOT NULL REFERENCES Attendance(AttendanceId),
 CheckInTime DATETIME2 NOT NULL,
 CheckOutTime DATETIME2 NULL,
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
 CONSTRAINT CK_Session_Time CHECK(CheckOutTime IS NULL OR CheckOutTime > CheckInTime)
);
CREATE UNIQUE INDEX UX_Attendance_OneOpenSession
 ON AttendanceSessions(AttendanceId) WHERE CheckOutTime IS NULL;
CREATE TABLE Holidays (
 HolidayId INT IDENTITY(1,1) PRIMARY KEY,
 HolidayDate DATE NOT NULL UNIQUE,
 HolidayName VARCHAR(150) NOT NULL,
 IsActive BIT NOT NULL DEFAULT 1
);
CREATE TABLE LeaveRequests (
 LeaveRequestId BIGINT IDENTITY(1,1) PRIMARY KEY,
 EmployeeId INT NOT NULL REFERENCES Employees(EmployeeId),
 FromDate DATE NOT NULL, ToDate DATE NOT NULL,
 LeaveType VARCHAR(30) NOT NULL, Reason VARCHAR(500) NULL,
 Status VARCHAR(20) NOT NULL DEFAULT 'Pending',
 ApprovedBy INT NULL REFERENCES Users(UserId),
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
 CONSTRAINT CK_Leave_Dates CHECK(ToDate >= FromDate),
 CONSTRAINT CK_Leave_Status CHECK(Status IN ('Pending','Approved','Rejected'))
);
CREATE TABLE AttendanceCorrectionRequests (
 CorrectionId BIGINT IDENTITY(1,1) PRIMARY KEY,
 AttendanceId BIGINT NOT NULL REFERENCES Attendance(AttendanceId),
 RequestedBy INT NOT NULL REFERENCES Users(UserId),
 Reason VARCHAR(500) NOT NULL,
 ProposedCheckIn DATETIME2 NULL, ProposedCheckOut DATETIME2 NULL,
 Status VARCHAR(20) NOT NULL DEFAULT 'Pending',
 ReviewedBy INT NULL REFERENCES Users(UserId),
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
 CONSTRAINT CK_Correction_Status CHECK(Status IN ('Pending','Approved','Rejected'))
);
CREATE TABLE AuditLogs (
 AuditId BIGINT IDENTITY(1,1) PRIMARY KEY,
 UserId INT NULL REFERENCES Users(UserId),
 Action VARCHAR(100) NOT NULL,
 TableName VARCHAR(100) NULL, RecordId VARCHAR(100) NULL,
 OldValue NVARCHAR(MAX) NULL, NewValue NVARCHAR(MAX) NULL,
 CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
CREATE TABLE SystemSettings (
 SettingKey VARCHAR(100) PRIMARY KEY,
 SettingValue NVARCHAR(500) NOT NULL
);
INSERT INTO Roles(RoleName) VALUES ('Admin'),('HR'),('Manager'),('Employee');
INSERT INTO Departments(DepartmentName) VALUES ('General');
INSERT INTO Shifts(ShiftName,StartTime,EndTime,GraceMinutes,BreakMinutes)
 VALUES ('General','09:00','18:00',10,60);
INSERT INTO SystemSettings(SettingKey,SettingValue)
 VALUES ('TimeZone','India Standard Time'),('AttendanceCutoff','23:59');
CREATE INDEX IX_Attendance_Date ON Attendance(AttendanceDate);
CREATE INDEX IX_Attendance_Employee_Date ON Attendance(EmployeeId,AttendanceDate);
CREATE INDEX IX_Audit_CreatedAt ON AuditLogs(CreatedAt);
GO
