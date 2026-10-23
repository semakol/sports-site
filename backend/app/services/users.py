from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, Conflict, NotFound
from app.core.security import hash_password, verify_password
from app.models import User
from app.models.enums import UserRole


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))


async def create_user(
    session: AsyncSession, email: str, password: str, full_name: str, role: UserRole = UserRole.team_rep
) -> User:
    if await get_by_email(session, email):
        raise Conflict("EMAIL_TAKEN", "Пользователь с таким email уже существует", field="email")
    user = User(email=email.lower(), password_hash=hash_password(password), full_name=full_name, role=role)
    session.add(user)
    await session.commit()
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await get_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "Неверный email или пароль")
    if not user.is_active:
        raise AppError(403, "USER_INACTIVE", "Учётная запись отключена")
    return user


async def list_users(
    session: AsyncSession, role: UserRole | None, search: str | None, limit: int, offset: int
) -> tuple[list[User], int]:
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    total = await session.scalar(select(func.count()).select_from(query.subquery()))
    users = await session.scalars(query.order_by(User.full_name, User.id).limit(limit).offset(offset))
    return list(users), total or 0


async def set_role(session: AsyncSession, actor: User, user_id: int, role: UserRole) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFound("Пользователь не найден")
    # Иначе администратор может случайно лишить систему последнего админа
    if user.id == actor.id and role != UserRole.admin:
        raise Conflict(
            "CANNOT_CHANGE_OWN_ROLE", "Нельзя снять роль администратора с самого себя", field="role"
        )
    user.role = role
    await session.commit()
    return user
