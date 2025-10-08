from typing import ClassVar
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel
from uuid6 import uuid7


# Identity schema: app_user
class AppUser(SQLModel, table=True):
		"""identity.app_user

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
		email: EmailStr = Field(unique=True, index=True, max_length=255)
		full_name: str | None = Field(default=None, max_length=255)
		hashed_password: str = Field(max_length=255)
		is_superuser: bool = Field(default=False)


# Asset schema: farm
class Farm(SQLModel, table=True):
		"""asset.farm

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

