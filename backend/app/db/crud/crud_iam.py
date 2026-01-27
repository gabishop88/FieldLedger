from pydantic import EmailStr
from sqlmodel import Session, select

from app.core.security import decode_token, get_password_hash, verify_password
from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    AppUser,
    PasswordReset,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserUpdateSelf,
)

CreateType = UserCreate | UserRegister
UpdateType = UserUpdate | UserUpdateSelf


class CRUDUser(CRUDBase[AppUser, CreateType, UpdateType]):
    def get_by_email(self, db: Session, email: EmailStr) -> AppUser | None:
        """### Returns the user (or None) associated withe email.
        Convienience method since it is done often.
        """
        return db.exec(select(AppUser).where(AppUser.email == email)).first()

    def authenticate(
        self, db: Session, email: EmailStr, password: str
    ) -> AppUser | None:
        """Get an `AppUser` record if the email and password match the database."""
        user = self.get_by_email(db, email)
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    def create(self, db: Session, new_record: CreateType) -> AppUser:
        record = AppUser.model_validate(
            new_record,
            update={"hashed_password": get_password_hash(new_record.password)},
        )
        self._safe_add(db, [record])
        return record

    def update(self, db: Session, record: AppUser, changes: UpdateType) -> AppUser:
        update_dict = changes.model_dump(exclude_unset=True)
        if "password" in update_dict:
            update_dict["hashed_password"] = get_password_hash(update_dict["password"])
        record.sqlmodel_update(update_dict)
        self._safe_add(db, [record])
        return record

    def reset_password(self, db: Session, reset: PasswordReset) -> AppUser | None:
        """Updates the password of the user whose id is contained in the `reset.token`.
        Returns `None` if the user could not be found.
        """
        user = db.get(AppUser, decode_token(reset.token))
        if user:
            user.hashed_password = get_password_hash(reset.new_password)
            self._safe_add(db, [user])
        return user


user = CRUDUser(AppUser)
