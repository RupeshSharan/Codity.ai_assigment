from pydantic import BaseModel, Field

from app.models import MemberRole
from app.schemas.common import Timestamped


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class OrganizationRead(Timestamped):
    id: str
    name: str
    slug: str
    owner_id: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None


class ProjectRead(Timestamped):
    id: str
    organization_id: str
    name: str
    slug: str
    description: str | None


class ProjectMemberRead(Timestamped):
    id: str
    project_id: str
    user_id: str
    role: MemberRole
