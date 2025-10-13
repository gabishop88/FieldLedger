from typing import ClassVar
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel
from uuid6 import uuid7

# ---------------------------------- Schema: identity ----------------------------------


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserPublic(UserBase):
    id: UUID


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=255)


class UserUpdateSelf(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=255)


class PasswordReset(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=255)


class AppUser(UserBase, table=True):
    """identity.app_user table

    Columns:
            - id: UUID PK
            - email: EmailStr, unique, indexed, not null
            - full_name: optional
            - hashed_password: required
            - is_superuser: bool
    """

    __tablename__: ClassVar[str] = "app_user"
    __table_args__: ClassVar[dict] = {"schema": "identity"}

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    hashed_password: str = Field(max_length=255)


# ----------------------------------- Schema: asset ------------------------------------


class Farm(SQLModel, table=True):
    """asset.farm table

    Columns:
            - id: UUID PK
            - name: varchar(255) not null
            - private: bool
            - description: text
    """

    __tablename__: ClassVar[str] = "farm"
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    name: str = Field(max_length=255)
    private: bool = Field(default=False)
    description: str | None = Field(default=None, sa_column=Column(Text))


# Reference schema: field_type
class FieldType(SQLModel, table=True):
    """ref.field_type

    Columns:
            - name: varchar(32) PK
            - description: text
    """

    __tablename__: ClassVar[str] = "field_type"
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    name: str = Field(primary_key=True, max_length=32)
    description: str | None = Field(default=None, sa_column=Column(Text))
