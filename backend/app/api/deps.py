"""### Available FastAPI Dependencies
See: https://fastapi.tiangolo.com/tutorial/dependencies/ for additional information.

To use one of the dependencies defined here:
```py
from app.api.deps import SomeSession, SomeUser
def endpoint_function(db: SomeSession, user: SomeUser): # For example
    ...
```
Where `SomeSession` can be:
* `ReadSession`: Read-only session to be used by anyone; cannot alter the database.
* `WriteSession`: Read/write (no auditability). Only if you can't have user logged in.
* `UserSession`: Just a `WriteSession`, except it makes sure there is a user logged in.
* `SuperuserSession`: Same as `UserSession` but enforces user.is_superuser=True.

and `SomeUser` can be:
* `CurrentUser`: Currently Authenticated User based on Auth header. Exception if no user
* `CurrentSuperuser`: same as `CurrentUser` but enforces user.is_superuser=True.
"""

import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, text

from app.core import security
from app.core.config import settings
from app.core.enums import ErrMsg
from app.db.connection import get_engine
from app.db.models import AppUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOTE: read/write_session calls 'RESET "app.current_user"' to prevent any missing errs.


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
        raise HTTPException(status.HTTP_403_FORBIDDEN, ErrMsg.FBDN_CRED)

    user = db.get(AppUser, key)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("AppUser", key))

    db.close()  # Close the readonly session that was only needed to get current user.
    return user


CurrentUser = Annotated[AppUser, Depends(get_current_user)]


def get_current_superuser(current_user: CurrentUser) -> AppUser:
    """Returns current user if they have superuser perms. Otherwise raises Exception."""
    if current_user is None or not current_user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, ErrMsg.FBDN_PRIV)
    return current_user


CurrentSuperuser = Annotated[AppUser, Depends(get_current_superuser)]


# ------------------------------- Read/Write DB Session --------------------------------


def write_session(request: Request) -> Generator[Session, None, None]:
    dry_run = request.headers.get("X-Dry-Run") == "true"
    with Session(get_engine()) as session:
        try:
            session.exec(text('RESET "app.current_user"'))  # type: ignore
            yield session
            session.rollback() if dry_run else session.commit()
        except Exception:
            session.rollback()
            raise


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


def write_session_with_superuser(
    db: WriteSession, user: CurrentSuperuser
) -> Generator[Session, None, None]:
    yield from write_session_with_user(db, user)


SuperuserSession = Annotated[Session, Depends(write_session_with_superuser)]
