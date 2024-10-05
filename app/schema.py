import datetime
import uuid
from string import ascii_letters, digits, punctuation

from pydantic import BaseModel, field_validator

PASSWORD_CHARS = ascii_letters + digits + punctuation + " "


class IdReturnBase(BaseModel):
    id: int


class GetAdvertisementResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    user_id: int
    created_at: datetime.datetime


class CreateAdvertisementRequest(BaseModel):
    title: str
    description: str
    price: float


class CreateAdvertisementResponse(IdReturnBase):
    pass


class UpdateAdvertisementRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None


class UpdateAdvertisementResponse(IdReturnBase):
    pass


class DeleteAdvertisementResponse(BaseModel):
    status: str


class BaseUser(BaseModel):
    name: str
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if len(value) < 8 or any(el not in PASSWORD_CHARS for el in value):
            raise ValueError(
                "password is too short or contains forbidden characters")
        return value


class LoginRequest(BaseUser):
    pass


class LoginResponse(BaseModel):
    token: uuid.UUID


class CreateUserRequest(BaseUser):
    pass


class CreateUserResponse(IdReturnBase):
    pass


class GetUserResponse(BaseModel):
    id: int
    name: str


class UpdateUserRequest(BaseUser):
    name: str = None
    password: str = None


class UpdateUserResponse(IdReturnBase):
    pass


class DeleteUserResponse(BaseModel):
    status: str
