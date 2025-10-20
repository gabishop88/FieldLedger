from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.api.deps import ReadSession
from app.core.config import settings
from app.core.security import create_access_token
from app.db import crud
from app.db.models import AppUser, Token

router = APIRouter(prefix="/account")


LoginForm = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post("/login/access-token")
def get_access_token(db: ReadSession, login_data: LoginForm) -> Token:
    user = crud.user.authenticate(db, login_data.username, login_data.password)
    if not user:
        if db.exec(select(AppUser).where(AppUser.email == login_data.username)).first():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect Password.")
        else:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Email(username) not found.")

    expires_after = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(access_token=create_access_token(user.id, expires_after))
