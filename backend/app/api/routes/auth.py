from fastapi import APIRouter, status

from app.api.deps import CurrentUser
from app.core.security import create_access_token
from app.db.session import SessionDep
from app.schemas.user import LoginRequest, RegisterRequest, Token, UserRead
from app.services import users as users_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, session: SessionDep) -> UserRead:
    """Регистрация. Новый пользователь получает роль team_rep, остальные роли выдаёт администратор."""
    user = await users_service.create_user(session, data.email, data.password, data.full_name)
    return UserRead.model_validate(user)


@router.post("/login")
async def login(data: LoginRequest, session: SessionDep) -> Token:
    user = await users_service.authenticate(session, data.email, data.password)
    return Token(access_token=create_access_token(user.id))


@router.get("/me")
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
