from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlmodel import func

from app.api.deps import (
    CurrentUser,
    ReadSession,
    SuperuserSession,
    UserSession,
    WriteSession,
)
from app.api.messages import ExeMsg
from app.core.config import settings
from app.core.security import create_access_token
from app.db import crud
from app.db.models import (
    AppUser,
    Paginated,
    Token,
    UserPublic,
    UserRegister,
    UserUpdate,
    UserUpdateSelf,
)

NAME_THRESHOLD = 0.4  # Similarity threshold for matching name when searching.

# Shorter names for the statuses I use explicitly
BAD_REQUEST = status.HTTP_400_BAD_REQUEST
FORBIDDEN = status.HTTP_403_FORBIDDEN
NOT_FOUND = status.HTTP_404_NOT_FOUND
CONFLICT = status.HTTP_409_CONFLICT

LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]  # Login Form type

router = APIRouter(prefix="/account")


# ------------------------------------- Auth Token -------------------------------------


@router.post("/login/access-token")
def get_access_token(db: ReadSession, login_data: LoginForm) -> Token:
    """### Provide an email (username) and password to get an auth token."""
    user = crud.user.authenticate(db, login_data.username, login_data.password)
    if not user:
        if crud.user.get_by_email(db, login_data.username):
            raise HTTPException(BAD_REQUEST, ExeMsg.BAD_PWD)
        else:
            raise HTTPException(
                NOT_FOUND, ExeMsg.NF.format("Email", login_data.username)
            )

    expires_after = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(user.id, expires_after),
        expires_min=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


# ---------------------------------- Modify Own User -----------------------------------


@router.get("/", response_model=UserPublic)
def get_your_user_info(user: CurrentUser) -> AppUser:
    """### See the account information for the user that is currently authenticated.
    To be 'authenticated', send the auth token in request "Auth" headers.

    If using /docs page, log in with the green 'Authorize' button.

    # TODO: add instructions for authentication via postman or manually via header.
    """
    return user


@router.post("/", response_model=UserPublic)
def register_user(db: WriteSession, user_in: UserRegister) -> AppUser:
    """### Register a new user account."""
    # TODO: Send a 'New Account' email? Add email verification? Use email-validator lib?
    return crud.user.create(db, user_in)


# TODO: Should I separate an update_password endpoint to just update that?
@router.patch("/", response_model=UserPublic)
def edit_your_user_info(
    db: UserSession, user: CurrentUser, edits: UserUpdateSelf
) -> AppUser:
    """### Edit the currently authorized user.
    Allows partial edits.

    Returns the updated user info.
    """
    return crud.user.update(db, user, edits)


@router.delete("/", response_model=UserPublic)
def delete_your_user_info(db: UserSession, user: CurrentUser) -> AppUser:
    """### Delete the currently authorized user.
    Returns user info as it was before deletion, it will not exist after calling.
    """
    if user.email == settings.FIRST_SUPERUSER:
        raise HTTPException(FORBIDDEN, ExeMsg.FBDN_DEL_1SU)
    return crud.user.delete(db, user)


# --------------------------------- Modify Other User ----------------------------------


@router.get("/search", response_model=Paginated[UserPublic])
def search_for_users(
    db: ReadSession,
    email: EmailStr | None = None,
    id: UUID | None = None,
    name: str | None = None,
    skip: int = 0,
    limit: int = 10,
) -> Paginated[AppUser]:
    """### Search for users.
    You can search with email/id (exact match only) or name (partial matches accepted).

    To prevent a huge dump of all users, provide at least one of these search options.

    Use `skip` and `limit` to paginate.
    The `count` is the total number of results found. If there are fewer users in `data`
    than the `count` would suggest, then there are additional pages of results.
    """
    if not any((email, id, name)):
        raise HTTPException(BAD_REQUEST, ExeMsg.BAD_EMPTY_SEARCH)
    # TODO: Should I restrict this to being able to be used by superusers only?
    # On one hand, privacy. On the other, looking up accts to give them permissions?

    filters = []
    if email:
        filters.append(AppUser.email == email)
    if id:
        filters.append(AppUser.id == id)
    if name:
        filters.append(func.similarity(AppUser.full_name, name) > NAME_THRESHOLD)

    return crud.user.get_paginated(db, skip, limit, *filters)


@router.patch("/{user_id}", response_model=UserPublic)
def edit_other_user(db: SuperuserSession, user_id: UUID, edits: UserUpdate) -> AppUser:
    """### Edit the data of another user.
    *MUST BE LOGGED IN AS A SUPERUSER*
    """
    other_user = db.get(AppUser, user_id)
    if not other_user:
        raise HTTPException(NOT_FOUND, ExeMsg.NF.format("AppUser", user_id))
    if edits.email and crud.user.get_by_email(db, edits.email):
        raise HTTPException(CONFLICT, ExeMsg.KEY_EXISTS.format("email", edits.email))

    return crud.user.update(db, other_user, edits)


@router.delete("/{user_id}", response_model=UserPublic)
def delete_other_user(db: SuperuserSession, user_id: UUID) -> AppUser:
    """### Delete another user.
    *MUST BE LOGGED IN AS A SUPERUSER*
    """
    other_user = db.get(AppUser, user_id)
    if not other_user:
        raise HTTPException(NOT_FOUND, ExeMsg.NF.format("AppUser", user_id))
    if other_user.email == settings.FIRST_SUPERUSER:
        raise HTTPException(FORBIDDEN, ExeMsg.FBDN_REM_1SU)
    return crud.user.delete(db, other_user)
