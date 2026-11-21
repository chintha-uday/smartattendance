from getpass import getpass
from app.database import Base, engine, SessionLocal
from app.models import Role, User
from app.security import hash_password

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for name in ["Admin", "HR", "Manager", "Employee"]:
            if not db.query(Role).filter_by(name=name).first():
                db.add(Role(name=name))
        db.commit()
        if db.query(User).filter_by(username="admin").first():
            print("An admin account already exists.")
            return
        username = input("Create administrator username [admin]: ").strip() or "admin"
        while True:
            password = getpass("Create administrator password (10+ chars): ")
            confirm = getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match.")
                continue
            try:
                hashed = hash_password(password)
                break
            except ValueError as exc:
                print(exc)
        role = db.query(Role).filter_by(name="Admin").one()
        db.add(User(username=username, password_hash=hashed, role_id=role.id))
        db.commit()
        print("Administrator created. Start the application with run.bat.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
