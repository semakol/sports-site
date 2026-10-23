from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.models.enums import UserRole

# Email храним в нижнем регистре, чтобы Ivan@Mail.ru и ivan@mail.ru были одним пользователем
Email = Annotated[EmailStr, AfterValidator(str.lower)]
FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class RegisterRequest(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)
    full_name: FullName


class LoginRequest(BaseModel):
    # Без строгой проверки формата: вход не должен ломаться, если правила валидации email поменяются
    email: Annotated[str, AfterValidator(str.lower)]
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: UserRole


class RoleUpdate(BaseModel):
    role: UserRole
