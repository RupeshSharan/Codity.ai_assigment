from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.db.session import get_db
from app.models import MemberRole, ProjectMember, User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthenticationError("Missing bearer token.")
    payload = decode_access_token(credentials.credentials)
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise AuthenticationError("User is not active.")
    return user


def require_project_role(
    db: Session, user: User, project_id: str, allowed_roles: set[MemberRole]
) -> ProjectMember:
    membership = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    ).scalar_one_or_none()
    if membership is None or membership.role not in allowed_roles:
        raise AuthorizationError("You do not have permission for this project.")
    return membership

