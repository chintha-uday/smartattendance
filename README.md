# Smart Attendance Management System

This repository contains **Smart Attendance Management System (SAMS)**, a browser-based attendance and leave-management application for small and medium-sized offices. It is an MVP designed for a local development environment or a controlled office-network pilot.

> **Current public deployment: synthetic demo only.** Do not enter real employee information into the hosted demo. This MVP still needs the production-hardening work listed in [Security, privacy, and production readiness](#12-security-privacy-and-production-readiness).

## Contents

1. [Project, development, and publishing locations](#1-project-development-and-publishing-locations)
2. [What the application does](#2-what-the-application-does)
3. [Roles and demo accounts](#3-roles-and-demo-accounts)
4. [Technology and architecture](#4-technology-and-architecture)
5. [Repository map](#5-repository-map)
6. [Local Windows setup](#6-local-windows-setup)
7. [Hosted demo and deployment](#7-hosted-demo-and-deployment)
8. [Data and database](#8-data-and-database)
9. [Tests and verification](#9-tests-and-verification)
10. [How to use the application](#10-how-to-use-the-application)
11. [Known limitations](#11-known-limitations)
12. [Security, privacy, and production readiness](#12-security-privacy-and-production-readiness)
13. [References](#13-references)

## 1. Project, development, and publishing locations

### Developed here

- **Local working copy:** `C:\Users\God\simple-web-app\smartattendance`
- **Development OS:** Windows
- **Development runtime:** Python 3.13 in a project-local `.venv`
- **Hosted runtime:** Python 3.12, pinned by [`.python-version`](./.python-version)
- **Source control:** Git, `main` branch

The local development database is SQLite (`smartattendance_dev.db`). The `.venv`, `.env`, and `*.db` files are excluded from Git by [`.gitignore`](./.gitignore); they are not published with the source.

### Shared source code

- **Public GitHub repository:** [chintha-uday/smartattendance](https://github.com/chintha-uday/smartattendance)
- **Branch:** [`main`](https://github.com/chintha-uday/smartattendance/tree/main)
- **Deployment setup commit:** [Prepare Smart Attendance hosted demo](https://github.com/chintha-uday/smartattendance/commit/9f912782115878afe548f2f40112d9f7721218c9)
- **Current PostgreSQL compatibility fix:** [Quote attendance constraint for PostgreSQL](https://github.com/chintha-uday/smartattendance/commit/41627fda312d71077c963f2eeb61125c67dd07d5)

The repository is **public**, so its source and documentation are visible to anyone. No local `.env`, database file, admin password, or Render database password is committed.

### Published application

- **Hosted demo / employee sign-in:** [https://smartattendance-demo.onrender.com/login](https://smartattendance-demo.onrender.com/login)
- **Health check:** [https://smartattendance-demo.onrender.com/health](https://smartattendance-demo.onrender.com/health)
- **Hosting platform:** Render
- **Render Blueprint:** [smartattendance-demo](https://dashboard.render.com/blueprint/exs-dc0n6dks728c73apkjeg)
- **Render web service:** [smartattendance-demo](https://dashboard.render.com/web/srv-dc0n733m8hqs73f1trr0)
- **Render PostgreSQL database:** [smartattendance-demo-db](https://dashboard.render.com/d/dpg-dc0n6ijm8hqs73f1siq0-a)
- **Blueprint configuration in this repository:** [`render.yaml`](./render.yaml)

The health endpoint was checked after deployment and returned `{"status":"ok","application":"Smart Attendance Demo"}`. The demo has also been checked by signing in with a sample employee and viewing that employee's attendance history.

### GitHub Pages status

**GitHub Pages is not enabled for this project.** Pages serves static websites; SAMS needs a running Python/FastAPI server and a database for sign-in, attendance, and leave workflows. The live app is therefore hosted on Render. The GitHub repository is for source code and version history, not the running app.

## 2. What the application does

The application provides a browser interface for attendance and basic employee administration:

- Admin, HR, Manager, and Employee roles.
- Employee creation, account creation, and deactivation.
- Shift assignment and grace-period settings.
- Employee check-in and check-out using the application server's clock.
- Daily duplicate check-in prevention.
- Late-arrival, early-departure, work-minute, and half-day calculations.
- Employee attendance history.
- Leave request submission and approval or rejection.
- Attendance CSV export for authorized roles.
- Audit-event recording for selected actions.
- Health-check endpoint for deployment monitoring.

Attendance is currently recorded as one check-in/check-out session per employee per local calendar day. The app does not yet automatically materialize daily leave, holiday, or absence records.

## 3. Roles and demo accounts

The application defines four roles: **Admin**, **HR**, **Manager**, and **Employee**. Route-level checks restrict several administrative actions to specific roles. Manager team scoping remains a known limitation; see [Known limitations](#11-known-limitations).

### Public demo logins

These are shared sample accounts with synthetic employee records. All three use the same public demo password:

| Username | Password |
|---|---|
| `demo.avery` | `DemoPass2026!` |
| `demo.sam` | `DemoPass2026!` |
| `demo.jordan` | `DemoPass2026!` |

Sign in at [the hosted demo](https://smartattendance-demo.onrender.com/login). Employee accounts can view their own sample attendance history. Because these credentials are public and shared, they are **not private accounts**: do not use them for real attendance or enter real employee details. The hosted demo seeds employee accounts, not an administrator account.

For a local installation, create your own administrator interactively using the instructions in [Local Windows setup](#6-local-windows-setup). There is no default admin password.

## 4. Technology and architecture

### Technology

- **Python 3.12+** application code.
- **FastAPI** HTTP routes and request handling.
- **Uvicorn** ASGI server.
- **SQLAlchemy 2** ORM and database metadata.
- **Jinja2** server-rendered HTML templates.
- **Bootstrap 5.3.3** page styling, loaded from its CDN.
- **Starlette signed-cookie sessions** for browser login state.
- **Argon2** password hashing.
- **SQL Server** for the documented office deployment, **SQLite** for local development, and **PostgreSQL** for the hosted Render demo.

Exact Python dependencies are listed in [`requirements.txt`](./requirements.txt). The configuration defaults and environment-variable names are in [`app/config.py`](./app/config.py) and [`.env.example`](./.env.example).

### Request and data flow

1. A user opens a page or submits a form in their browser.
2. FastAPI routes in [`app/main.py`](./app/main.py) validate the session and role where applicable.
3. SQLAlchemy models in [`app/models.py`](./app/models.py) read or update the configured database.
4. Jinja2 templates in [`app/templates/`](./app/templates/) render the browser pages.
5. Selected actions are added to the audit log by [`app/audit.py`](./app/audit.py).

At startup, the app creates missing SQLAlchemy tables and ensures the standard roles, a General department, and a General shift exist. The hosted start command runs the explicitly gated synthetic-data seeder before Uvicorn starts.

### Main browser routes

| Route | Purpose |
|---|---|
| `/login`, `/logout` | Sign in and sign out |
| `/dashboard` | Role-specific employee or management dashboard |
| `/attendance` | Attendance history |
| `/attendance/check-in`, `/attendance/check-out` | Record an employee's daily attendance |
| `/employees` | Admin/HR employee management |
| `/shifts` | Admin/HR shift management |
| `/leaves` | View or apply for leave |
| `/leaves/{leave_id}/decision` | Admin/HR/Manager leave decision |
| `/reports.csv` | Download the CSV attendance report for authorized roles |
| `/health` | Deployment health check |

## 5. Repository map

| Path | Contents |
|---|---|
| [`app/main.py`](./app/main.py) | FastAPI app, routes, startup initialization, attendance and leave workflows |
| [`app/models.py`](./app/models.py) | SQLAlchemy models for users, employees, shifts, attendance, leave, and audit events |
| [`app/database.py`](./app/database.py) | Engine, database URL normalization, and SQLAlchemy sessions |
| [`app/config.py`](./app/config.py) | Environment-backed settings |
| [`app/security.py`](./app/security.py) | Password hashing/verification, session-user lookup, and role guards |
| [`app/audit.py`](./app/audit.py) | Audit log helper |
| [`app/setup_admin.py`](./app/setup_admin.py) | Interactive local first-admin setup |
| [`app/seed_demo.py`](./app/seed_demo.py) | Opt-in, idempotent generator for synthetic demo accounts and attendance |
| [`app/templates/`](./app/templates/) | Jinja2 pages |
| [`app/static/css/app.css`](./app/static/css/app.css) | Application styles |
| [`database/schema.sql`](./database/schema.sql) | SQL Server schema and initial role/department/shift records |
| [`scripts/install.bat`](./scripts/install.bat) | Windows dependency/virtual-environment installer |
| [`scripts/run.bat`](./scripts/run.bat) | Windows local server launcher |
| [`scripts/backup_sqlserver.bat`](./scripts/backup_sqlserver.bat) | SQL Server backup script |
| [`render.yaml`](./render.yaml) | Render Blueprint for the demo web service and PostgreSQL database |
| [`tests/`](./tests/) | Smoke test, database URL tests, and synthetic-seed tests |

## 6. Local Windows setup

### Requirements

- Windows 10/11 Pro or Windows Server.
- Python 3.12 or newer.
- For SQL Server: SQL Server Express/Standard and Microsoft ODBC Driver 18.
- Optional `sqlcmd` for the backup script.

### Install and run with the project scripts

In Command Prompt, open the repository folder and run:

```bat
scripts\install.bat
```

Edit `.env` and set `DB_URL`. For SQL Server integrated authentication, an example is:

```text
DB_URL=mssql+pyodbc://@localhost/SmartAttendanceDB?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
```

For a local development smoke test, SQLite is the default:

```text
DB_URL=sqlite:///./smartattendance_dev.db
```

Create your own administrator; the command prompts for a username and a password of at least 10 characters:

```bat
.venv\Scripts\python -m app.setup_admin
```

Start the app:

```bat
scripts\run.bat
```

Browse to [http://127.0.0.1:8000](http://127.0.0.1:8000). The run script binds to `0.0.0.0:8000` for office-network use; allow inbound connections only from the intended office network.

### Manual virtual environment commands

If the Windows Python launcher (`py`) is unavailable, create the environment with the installed `python` command:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.setup_admin
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### SQL Server schema choice

Choose one schema setup path:

1. Run [`database/schema.sql`](./database/schema.sql) in SQL Server Management Studio, then create the admin with `app.setup_admin`; **or**
2. Grant the setup identity permission to create tables and let SQLAlchemy create missing metadata on startup.

Do not run schema creation paths against an existing populated database without first checking its objects and data. For production SQL Server, use a dedicated least-privilege service identity and a trusted SQL Server certificate.

## 7. Hosted demo and deployment

### Render setup

[`render.yaml`](./render.yaml) defines:

- A free Render Python web service named `smartattendance-demo`.
- A free managed PostgreSQL database named `smartattendance-demo-db`.
- A generated `APP_SECRET_KEY`.
- `APP_ENV=production` and `APP_DEMO_DATA=1`.
- A health check at `/health`.
- A startup command that seeds synthetic sample records, then runs Uvicorn on Render's `$PORT`.

The seeder in [`app/seed_demo.py`](./app/seed_demo.py) refuses to run unless `APP_DEMO_DATA=1`. It does not seed a database that already contains employees or attendance and safely returns if all demo employees already exist. It creates three demo employee accounts and attendance for five recent weekdays.

The hosted app uses PostgreSQL, not the local SQLite database. [`app/database.py`](./app/database.py) normalizes Render's `postgres://`/`postgresql://` URL forms to the SQLAlchemy `postgresql+psycopg://` driver. The attendance-session time constraint is quoted for PostgreSQL's case-sensitive column names.

### Recreate or inspect the deployment

1. Sign in to [Render](https://dashboard.render.com/).
2. Select **New → Blueprint**.
3. Connect the public repository or enter `https://github.com/chintha-uday/smartattendance`.
4. Select the `main` branch and root `render.yaml`.
5. Review the listed web service and database, then apply the Blueprint.
6. Open the hosted app at [smartattendance-demo.onrender.com](https://smartattendance-demo.onrender.com/login) and confirm `/health` returns `status: ok`.

The current Render Blueprint and service use a public-repository connection. The initial deployments were manually initiated in the Render dashboard; do not assume pushes automatically redeploy. After a code change, check Render's deploy status and use the dashboard's **Manual Deploy → Deploy latest commit** or sync the Blueprint as appropriate.

### Free-tier behavior and data retention

- Render's free web service spins down after inactivity; its first request after sleeping can take about a minute.
- Free-service local files are ephemeral; the hosted database is PostgreSQL, not a local database file.
- Render currently marks the free PostgreSQL database to expire on **December 21, 2026**. It will be deleted unless upgraded. Confirm current dates and plan details in the [database dashboard](https://dashboard.render.com/d/dpg-dc0n6ijm8hqs73f1siq0-a) before relying on its data.
- Free plans are intended for demos and testing, not production attendance records.

## 8. Data and database

The ORM models include roles, departments, shifts, employees, user accounts, attendance days, attendance sessions, leave requests, holidays, audit logs, and system settings.

The SQL Server schema also defines an attendance correction request table, but its approval workflow is not implemented in the app UI yet.

Database choices by environment:

| Environment | Database |
|---|---|
| Local development default | SQLite (`smartattendance_dev.db`) |
| Documented office deployment | SQL Server |
| Public demo on Render | Managed PostgreSQL |

The hosted demo is publicly reachable and uses shared employee credentials. Keep its data synthetic. Do not copy real employee records into the demo database, use the public demo accounts for real users, or treat the free database as a backup.

## 9. Tests and verification

Run the test suite from the repository root after installing the requirements:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests cover the health endpoint, database URL normalization, and that demo seeding is opt-in and idempotent. The deployment was also checked by requesting the hosted health endpoint and signing in to view a sample employee's attendance history.

## 10. How to use the application

### Employee

1. Open the [hosted sign-in page](https://smartattendance-demo.onrender.com/login) for the online demo, or the local app URL for a local installation.
2. Sign in with an employee account.
3. Use the dashboard to check in and check out.
4. Use **Attendance** to view the account's own attendance history.
5. Use **Leaves** to submit a leave request and view its status.

### Local administrator or HR

1. Sign in with the local administrator account created using `app.setup_admin`.
2. Use **Employees** to create an employee and their login. Provide a unique username and an initial password of at least 10 characters.
3. Assign the employee a department and shift.
4. Use **Shifts** to manage shift definitions.
5. Review attendance and leave requests; authorized roles can download **Export CSV**.

The hosted demo is deliberately limited to generated employee accounts and is not configured with a shared administrator login.

## 11. Known limitations

- One attendance check-in/check-out session per employee per local calendar day.
- Attendance timestamps use the server's local clock; production should use UTC storage and explicit company-time-zone conversion.
- Overnight shifts and daylight-saving transitions need review.
- Automatic daily absence, holiday, and leave materialization is not implemented.
- Attendance correction approval UI and holiday administration UI are not implemented.
- Manager team-scope authorization must be designed and verified before live use.
- Login throttling, password reset, and forced first-login password changes are not implemented.
- Browser forms do not yet have CSRF protection.
- CSV export exists; filtered report UI and formatted XLSX export are future work.
- The project is an MVP; passing the current tests does not certify it for production.

## 12. Security, privacy, and production readiness

**Do not use the public demo for real employees or sensitive personal information.** Its employee usernames and password are published above, it is internet-accessible, and users share a synthetic-data demo database.

Before deploying for live attendance, at minimum:

- Implement and test CSRF protection for every state-changing browser form.
- Add login throttling and secure account/password recovery.
- Require changing the initial password at first login.
- Review authorization for every route, especially manager team scope, employee data access, and CSV export.
- Review and harden cookie/session settings and secret rotation for the actual deployment.
- Configure and verify HTTPS, least-privilege database access, network controls, encrypted off-site backups, and tested restoration.
- Define retention, access, incident-response, and data-processing policies for employee attendance data.
- Use a supported production service/deployment process with dependency locking and monitoring.
- Validate company timezone and overnight-shift behavior; test database migrations and backups.
- Upgrade from expiring demo/free resources to a suitable production plan before keeping business data.

The Render `APP_ENV=production` setting enables secure-only session cookies; it does **not** make this MVP production-ready by itself.

## 13. References

### Project source and deployment

- [GitHub repository](https://github.com/chintha-uday/smartattendance)
- [Current `main` source tree](https://github.com/chintha-uday/smartattendance/tree/main)
- [Render Blueprint specification in this repo](./render.yaml)
- [Render-hosted demo](https://smartattendance-demo.onrender.com/login)
- [Render web-service dashboard](https://dashboard.render.com/web/srv-dc0n733m8hqs73f1trr0)
- [Render PostgreSQL dashboard and expiry details](https://dashboard.render.com/d/dpg-dc0n6ijm8hqs73f1siq0-a)
- [Render Blueprint dashboard](https://dashboard.render.com/blueprint/exs-dc0n6dks728c73apkjeg)
- [GitHub Pages information](https://docs.github.com/pages/getting-started-with-github-pages/what-is-github-pages)

### Framework and platform documentation

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Uvicorn documentation](https://www.uvicorn.org/)
- [SQLAlchemy 2.0 documentation](https://docs.sqlalchemy.org/en/20/)
- [Jinja documentation](https://jinja.palletsprojects.com/)
- [Argon2 Password Hashing](https://argon2-cffi.readthedocs.io/)
- [Python documentation](https://docs.python.org/3/)
- [Render Blueprints](https://render.com/docs/blueprint-spec)
- [Render Python version configuration](https://render.com/docs/python-version)
- [Render PostgreSQL](https://render.com/docs/postgresql-creating-connecting)
- [Render free instance limitations](https://render.com/docs/free)

### License

No license file is currently included in this repository. Do not assume the source is licensed for reuse or redistribution; contact the repository owner if you need permission.
