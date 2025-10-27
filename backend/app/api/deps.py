import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, text

from app.core import security
from app.core.config import settings
from app.db.connection import get_engine
from app.db.models import AppUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Usage Notes:
# if an endpoint function needs a database session, authenticated user, etc:
# `def endpoint_function_name(db: SomeSession, user: UserType):`

# Where `SomeSession` can be:
#   - ReadSession: gives a readonly session, does not require a user, and is safe (guarenteed not to edit data)
#   - WriteSession: this is an unauthenticated session that can read/write data.
#       this should only be used to write data when you explicitly do not need an authorized user to edit the data (very rare).
#   - UserSession: This is the most common type of session, you can read/write data, but it requires a valid auth header.

# And `UserType` can be:
#   - CurrentUser: Gives the iam.app_user record that is associated with the id found in the AccessToken, which is in the auth header.
#   - CurrentSuperuser: Gives the CurrentUser if they are a superuser (error if not).

# Helpful logging:
# logger.info(f'Location {int(session.exec(text("SELECT pg_backend_pid();")).first()[0])}') # type: ignore Currrent Session pid
# logger.info(json.dumps(list(map(tuple, session.exec(text("SELECT pid, usename, state, query FROM pg_stat_activity WHERE usename ILIKE 'fieldledger_%';")).all())), indent=2)) # type: ignore All Sessions


# --------------------------- Auth Token from Request Header ---------------------------

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/account/login/access-token"
)
AccessToken = Annotated[str, Depends(reusable_oauth2)]

# -------------------------------- Read-only DB Session --------------------------------


def read_session() -> Generator[Session, None, None]:
    with Session(get_engine(settings.READONLY_DATABASE_URI)) as session:
        session.exec(text('RESET "app.current_user"'))  # type: ignore
        yield session


ReadSession = Annotated[Session, Depends(read_session)]

# --------------------------- AppUser Record From Auth Token ---------------------------


def get_current_user(db: ReadSession, token: AccessToken) -> AppUser:
    """Returns current user if the header contains a valid auth token."""
    key = security.decode_token(token)
    if key is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Could not validate credentials")

    user = db.get(AppUser, key)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    db.close()  # Close the readonly session that was just needed to get the current user.
    return user


CurrentUser = Annotated[AppUser, Depends(get_current_user)]


def get_current_superuser(current_user: CurrentUser) -> AppUser:
    """Returns current user if they have superuser perms. Otherwise raises Exception."""
    if current_user is None or not current_user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User does not have priveleges.")
    return current_user


CurrentSuperuser = Annotated[AppUser, Depends(get_current_superuser)]


# ------------------------------- Read/Write DB Session --------------------------------


def write_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        session.exec(text('RESET "app.current_user"'))  # type: ignore
        yield session
        session.commit()

        # TODO: Set the session variable? How can I test it?
        # TODO: How can I check that an RLS policy or trigger func, etc. will see the session var correctly?
        # TODO: Should I do RLS policy or check for permissions manually in python?
        # TODO: Should this function only yield a session if you are logged in?
        # if user:
        # TODO: Should I commit once here, or commit when I make a change?


WriteSession = Annotated[Session, Depends(write_session)]


def write_session_with_user(
    db: WriteSession, user: CurrentUser
) -> Generator[Session, None, None]:
    """### Get a read/write database that also requires the user is authenticated.
    This also sets the `app.current_user` session variable which enables postgresql RLS.
    """
    db.exec(text(f"SET SESSION \"app.current_user\" = '{user.id}'"))  # type: ignore
    yield db


UserSession = Annotated[Session, Depends(write_session_with_user)]
