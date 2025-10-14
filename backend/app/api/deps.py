from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, text

from app.core import security
from app.core.config import settings
from app.db.connection import get_engine
from app.db.models import AppUser

# --------------------------- Auth Token from Request Header ---------------------------

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/account/login/access-token"
)
AccessToken = Annotated[str, Depends(reusable_oauth2)]

# -------------------------------- Read-only DB Session --------------------------------


def read_session() -> Generator[Session, None, None]:
    with Session(get_engine(settings.READONLY_DATABASE_URI)) as session:
        yield session


ReadSession = Annotated[Session, Depends(read_session)]

# --------------------------- AppUser Record From Auth Token ---------------------------


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


# ------------------------------- Read/Write DB Session --------------------------------


def write_session(user: CurrentUser) -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        try:
            # TODO: Set the session variable? How can I test it?
            # TODO: Make an endpoint that just returns the current setting of the session var?
            # TODO: How can I check that an RLS policy or trigger func, etc. will see the session var correctly?
            # TODO: Should I do RLS policy or check for permissions manually in python?
            # TODO: Should I set up the FIRST_SUPERUSER in db init or something, or should I insert it myself and save it as a data backup? (probably the former option)
            if user:
                session.exec(text(f"SET SESSION \"app.current_user\" = '{user.id}'"))  # type: ignore
            yield session
            session.commit()
            # TODO: Should I commit once here, or commit when I make a change?
        except Exception as e:
            session.rollback()
            raise e


WriteSession = Annotated[Session, Depends(write_session)]
