from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db, User
from app.errors import ConflictException, UnauthorizedException
from app.repositories import UserRepository
from app.schemas import Token, UserCreate, UserResponse, UserLogin
from app.security import (
    create_access_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication & Users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    user_repo = UserRepository(db)

    if user_repo.get_by_username(user_in.username):
        raise ConflictException(detail="Username already registered")

    if user_repo.get_by_email(user_in.email):
        raise ConflictException(detail="Email already registered")

    new_user = user_repo.create(user_in)
    return new_user


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password form login endpoint returning a Bearer JWT."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UnauthorizedException(detail="Incorrect username or password")

    if not user.is_active:
        raise UnauthorizedException(detail="User is inactive")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-json", response_model=Token)
def login_with_json(login_data: UserLogin, db: Session = Depends(get_db)):
    """Convenience JSON login endpoint returning a Bearer JWT."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(login_data.username)

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise UnauthorizedException(detail="Incorrect username or password")

    if not user.is_active:
        raise UnauthorizedException(detail="User is inactive")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Get profile information for the authenticated user."""
    return current_user
