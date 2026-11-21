# Smart Attendance Management System (SAMS) v1.0

A local-network employee attendance application for 10–100 employees.
Stack: FastAPI, SQLAlchemy, SQL Server, Bootstrap, Jinja2.

## Included
- Admin/HR/Manager/Employee roles
- Employee creation and deactivation
- Web check-in and check-out using server time
- Duplicate daily check-in prevention
- Late arrival calculation using assigned shift/grace period
- Employee attendance history
- Leave request and approval
- Shift management
- CSV attendance export
- Audit event logging
- Windows installation/run/SQL backup scripts

## Important implementation notes
This is an MVP starter release. Before production use, complete the hardening checklist below:
- Add CSRF protection to all state-changing browser forms.
- Configure HTTPS with an internal certificate/reverse proxy.
- Add attendance correction approval UI and holiday administration UI.
- Add automatic absence finalization and shift assignment history.
- Add login throttling, password reset and forced first-login password change.
- Restrict SQL Server network access to the application host.
- Configure off-machine encrypted backups and test restore.
- Review manager team-scope authorization and employee data access.
- Configure service startup under a dedicated Windows service identity.
- Review date/time handling for overnight shifts and daylight-saving zones.
- Use a production WSGI/ASGI service manager and pinned dependency lock.

## 1. Requirements
- Windows 10/11 Pro or Windows Server
- Python 3.12+
- SQL Server Express / Standard
- Microsoft ODBC Driver 18 for SQL Server
- Optional `sqlcmd` for backup script

## 2. Install
Open Command Prompt in the project folder:
1. Run `scripts\install.bat`
2. Edit `.env` and configure `DB_URL`.
3. For SQL Server integrated authentication, an example is:

`mssql+pyodbc://@localhost/SmartAttendanceDB?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes`

The Windows identity running the application needs appropriate database permissions. For production, use a dedicated least-privilege service identity and a trusted SQL Server certificate.

For a quick development smoke test only, use:
`DB_URL=sqlite:///./smartattendance_dev.db`

4. Create the first administrator:
` .venv\Scripts\python -m app.setup_admin `
5. Start:
` scripts\run.bat `
6. Browse to `http://127.0.0.1:8000`.

## 3. SQL Server setup
Either:
- Create `SmartAttendanceDB` and run `database/schema.sql` in SSMS, OR
- Grant the application setup identity permission to create the tables; the SQLAlchemy metadata will create missing tables on startup.

Do not run both schema creation paths against an already-populated database without checking existing objects. For a clean deployment, prefer `database/schema.sql` then create the administrator with the setup command.

## 4. Office LAN
Set a static/reserved server IP, configure `APP_HOST=0.0.0.0`, then allow inbound TCP 8000 only from the office subnet. Employees browse to `http://SERVER-IP:8000` during pilot testing. For production, put the app behind HTTPS using IIS/Caddy and a trusted internal certificate. Do not expose SQL Server port 1433 to employee devices or the internet.

## 5. Backup
Run `scripts\backup_sqlserver.bat` from an account permitted to back up the database. Copy backups to a separate protected device/location and periodically test restoration.

## 6. Tests
Activate the virtual environment and run:
`pytest -q`

## 7. Default shift
General: 09:00–18:00, 10-minute grace period, 60-minute break. Configure before onboarding employees.

## 8. Known MVP limitations
- Attendance is currently one check-in/check-out session per employee per local calendar day.
- The current app uses the server's local clock; keep the office server time zone set to India Standard Time. Production enhancement should use UTC storage plus explicit company timezone conversion.
- Leave requests can be submitted and approved, but automatic daily leave/holiday/absence materialization is not yet implemented.
- The correction request table is in the SQL schema, but the approval workflow UI is not yet implemented.
- CSV export is implemented; XLSX formatting and filtered report UI are future enhancements.
- Manager team scoping should be configured before using manager accounts in a live company.

## 9. Hosted demo (Render)
The included `render.yaml` deploys a synthetic-data demo with a Render web service and PostgreSQL database. In Render, choose **New → Blueprint**, select this repository, and apply the blueprint. Render provides the public URL after the first deployment.

Demo accounts (`DemoPass2026!`):
- `demo.avery`
- `demo.sam`
- `demo.jordan`

Each employee account can view its own sample attendance history. The demo database contains only generated sample records; do not enter real employee information. Render free web services sleep when idle, and free PostgreSQL databases expire after 30 days. This deployment is for demonstration only, not production attendance tracking.
