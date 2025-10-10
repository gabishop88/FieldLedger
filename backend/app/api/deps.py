from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.db import engine, ro_engine
from app.db.models import AppUser

# --------------------------------- Database Sessions ----------------------------------


def read_session() -> Generator[Session, None, None]:
    with Session(ro_engine) as session:
        yield session


def write_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e


ReadSession = Annotated[Session, Depends(read_session)]
WriteSession = Annotated[Session, Depends(write_session)]

# ----------------------------------- Users and Auth -----------------------------------

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/account/login/access-token"
)
AccessToken = Annotated[str, Depends(reusable_oauth2)]


def get_user_by_token(db: ReadSession, token: AccessToken) -> AppUser | None:
    """Returns current user if the header contains a valid auth token."""
    key = security.decode_token(token)
    if key is None:
        return None

    user = db.get(AppUser, key)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    return user


CurrentUser = Annotated[AppUser, Depends(get_user_by_token)]


def get_current_superuser(current_user: CurrentUser) -> AppUser:
    """Returns current user if they have superuser perms. Otherwise raises Exception."""
    if current_user is None or not current_user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User does not have priveleges")
    return current_user


CurrentSuperuser = Annotated[AppUser, Depends(get_current_superuser)]
