from app import app
from app.models import db, User, RoleEnum, RankEnum
from datetime import datetime

def create_user():
    with app.app_context():
        username = input("Enter username: ")
        print(f"Username entered: {username}")

        email = input("Enter email: ")
        print(f"Email entered: {email}")

        password = input("Enter password: ")
        print("Password entered")

        first_name = input("Enter first name: ")
        print(f"First name entered: {first_name}")

        last_name = input("Enter last name: ")
        print(f"Last name entered: {last_name}")

        role = input("Enter role (admin, teacher, member): ").upper()
        if role not in RoleEnum.__members__:
            print("Invalid role. Defaulting to MEMBER.")
            role = RoleEnum.MEMBER

        rank = input("Enter rank (kein, bronze, silber, gold, platin): ").upper()
        if rank not in RankEnum.__members__:
            print("Invalid rank. Defaulting to KEIN.")
            rank = RankEnum.KEIN

        active_from = input("Enter active from date (YYYY-MM-DD) or leave blank: ")
        active_from = datetime.strptime(active_from, '%Y-%m-%d') if active_from else None

        active_until = input("Enter active until date (YYYY-MM-DD) or leave blank: ")
        active_until = datetime.strptime(active_until, '%Y-%m-%d') if active_until else None

        if User.query.filter_by(username=username).first():
            print("Username already exists.")
            return

        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=RoleEnum[role],
            rank=RankEnum[rank],
            active=True,
            active_from=active_from,
            active_until=active_until
        )
        new_user.set_password(password)  # Assuming you have a method to set hashed password
        db.session.add(new_user)
        db.session.commit()
        print(f"User {username} created successfully.")

if __name__ == "__main__":
    create_user()