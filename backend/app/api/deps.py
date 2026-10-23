from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import Forbidden, Unauthorized
from app.core.security import decode_access_token
from app.db.session import SessionDep
from app.models import User
from app.models.enums import UserRole

# auto_error=False: без токена отвечаем своим 401 в едином формате ошибок
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise Unauthorized()
    user_id = decode_access_token(credentials.credentials)
    user = await session.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise Unauthorized("Токен недействителен или истёк", code="INVALID_TOKEN")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole):
    """Пускает только пользователей с одной из ролей: Depends(require_roles(UserRole.admin))."""

    async def checker(user: CurrentUser) -> User:
        if user.role not in roles:
            raise Forbidden()
        return user

    return checker
