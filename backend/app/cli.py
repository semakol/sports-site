"""Служебные команды.

Создать пользователя с любой ролью (например, первого администратора):
    python -m app.cli create-user --email admin@example.com --full-name "Админ" --role admin
Пароль спрашивается в консоли, чтобы не попадал в историю команд.
"""

import argparse
import asyncio
import getpass

from pydantic import TypeAdapter, ValidationError

from app.core.errors import AppError
from app.db.session import SessionLocal, engine
from app.models.enums import UserRole
from app.schemas.user import Email
from app.services.users import create_user


async def _create_user(email: str, full_name: str, role: UserRole, password: str) -> None:
    async with SessionLocal() as session:
        user = await create_user(session, email, password, full_name, role)
        print(f"Создан пользователь #{user.id} {user.email} с ролью {user.role}")
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-user", help="создать пользователя с заданной ролью")
    create.add_argument("--email", required=True)
    create.add_argument("--full-name", required=True)
    create.add_argument("--role", choices=[r.value for r in UserRole], default=UserRole.admin.value)
    args = parser.parse_args()
    try:
        email = TypeAdapter(Email).validate_python(args.email)
    except ValidationError:
        parser.error(f"некорректный email: {args.email}")

    password = getpass.getpass("Пароль: ")
    if len(password) < 8:
        parser.error("пароль должен быть не короче 8 символов")
    try:
        asyncio.run(_create_user(email, args.full_name, UserRole(args.role), password))
    except AppError as e:
        parser.exit(1, f"Ошибка: {e.message}\n")


if __name__ == "__main__":
    main()
