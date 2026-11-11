"""Auth endpoints in the format used by frontend/client (POST /api/auth/register|login|logout, GET /api/auth/me).
The classic OAuth2 endpoints under /api/v1/auth stay untouched."""
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import Location, LocationMember, User, get_db
from app.errors import ConflictException, UnauthorizedException, iso, ok
from app.repositories import UserRepository
from app.schemas import UserCreate
from app.security import create_access_token, get_current_user, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth (frontend API)"])


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def _user_dict(u: User, with_created: bool = True) -> dict:
    data = {"id": str(u.id), "username": u.username, "email": u.email, "role": u.role}
    if with_created:
        data["createdAt"] = iso(u.created_at)
    return data


def _token(u: User) -> str:
    return create_access_token(data={"sub": u.username, "role": u.role})


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_username(body.username):
        raise ConflictException("Username already registered")
    if db.query(User).filter(func.lower(User.email) == body.email.lower()).first():
        raise ConflictException("Email already registered")
    user = repo.create(UserCreate(username=body.username, email=body.email.lower(), password=body.password))
    return ok({"message": "User registered successfully", "token": _token(user), "user": _user_dict(user, False)})


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == body.email.lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password")
    if not user.is_active:
        raise UnauthorizedException("User is inactive")
    return ok({"message": "Login successful", "token": _token(user), "user": _user_dict(user)})


@router.post("/logout")
def logout(_: User = Depends(get_current_user)):
    # JWT is stateless: the client just drops the token.
    return ok({"message": "Logged out"})


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned = [l.id for l in db.query(Location.id).filter(Location.admin_id == user.id)]
    joined = [m.location_id for m in db.query(LocationMember).filter(LocationMember.user_id == user.id)]
    accessible = list(dict.fromkeys(owned + joined))
    return ok({
        **_user_dict(user),
        "ownedLocationIds": [str(i) for i in owned],
        "accessibleLocationIds": [str(i) for i in accessible],
    })
