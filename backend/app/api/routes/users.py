from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_roles
from app.db.session import SessionDep
from app.models import User
from app.models.enums import UserRole
from app.schemas.common import Page
from app.schemas.user import RoleUpdate, UserRead
from app.services import users as users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(
    session: SessionDep,
    _: Annotated[User, Depends(require_roles(UserRole.admin, UserRole.organizer))],
    role: UserRole | None = None,
    search: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[UserRead]:
    """Список пользователей. Организатору нужен, чтобы выбрать куратора на матч."""
    users, total = await users_service.list_users(session, role, search, limit, offset)
    return Page(items=[UserRead.model_validate(u) for u in users], total=total)


@router.patch("/{user_id}/role")
async def update_role(
    user_id: int,
    data: RoleUpdate,
    session: SessionDep,
    admin: Annotated[User, Depends(require_roles(UserRole.admin))],
) -> UserRead:
    user = await users_service.set_role(session, admin, user_id, data.role)
    return UserRead.model_validate(user)
