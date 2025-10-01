from uuid import UUID

from pydantic import EmailStr
from sqlmodel import Field, SQLModel
from uuid6 import uuid7


# # Shared Properties
# class UserBase(SQLModel):
#     email: EmailStr = Field(unique=True, index=True, max_length=127)
#     full_name: str | None = Field(default=None, max_length=127)
#     is_superuser: bool = False


# # Properties available when creating a `User`
# class UserCreate(UserBase):
#     password: str = Field(min_length=8, max_length=32)


# # TODO: More User models

# class User(UserBase, table=True):
#     id: UUID = Field(default_factory=uuid7, primary_key=True)
#     hashed_password: str
