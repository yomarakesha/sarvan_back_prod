import getpass
from app import create_app
from extensions import db
from models.admin import Admin

def create_initial_admin():
    app = create_app()
    with app.app_context():
        print("--- Создание нового администратора ---")
        username = input("Введите логин (username): ")

        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            print(f"Ошибка: Администратор с логином '{username}' уже существует.")
            return

        password = getpass.getpass("Введите пароль: ")
        confirm_password = getpass.getpass("Повторите пароль: ")

        if password != confirm_password:
            print("Ошибка: Пароли не совпадают.")
            return

        new_admin = Admin(username=username)
        new_admin.set_password(password)

        try:
            db.session.add(new_admin)
            db.session.commit()
            print(f"Успех! Администратор '{username}' успешно создан.")
        except Exception as e:
            db.session.rollback()
            print(f"Произошла ошибка при сохранении в базу: {e}")


if __name__ == "__main__":
    create_initial_admin()