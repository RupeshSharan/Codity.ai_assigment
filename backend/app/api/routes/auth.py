from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.exceptions import AuthenticationError, DomainError
from app.db.session import get_db
from app.models import MemberRole, Organization, ProjectMember, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.utils.slug import slugify

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise DomainError("A user with this email already exists.", status_code=409)
    user = User(email=email, full_name=payload.full_name, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    organization = Organization(
        name=payload.organization_name,
        slug=_unique_org_slug(db, payload.organization_name),
        owner_id=user.id,
    )
    db.add(organization)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.id, {"email": user.email}))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")
    return TokenResponse(access_token=create_access_token(user.id, {"email": user.email}))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def _unique_org_slug(db: Session, name: str) -> str:
    base = slugify(name)
    slug = base
    index = 2
    while db.execute(select(Organization.id).where(Organization.slug == slug)).scalar_one_or_none():
        slug = f"{base}-{index}"
        index += 1
    return slug

