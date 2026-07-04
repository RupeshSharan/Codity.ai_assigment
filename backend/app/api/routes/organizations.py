from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_project_role
from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.session import get_db
from app.models import MemberRole, Organization, Project, ProjectMember, RetryPolicy, User
from app.models.enums import RetryStrategy
from app.schemas.organization import OrganizationCreate, OrganizationRead, ProjectCreate, ProjectRead
from app.utils.slug import slugify

router = APIRouter()


@router.get("", response_model=list[OrganizationRead])
def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Organization]:
    project_orgs = (
        select(Project.organization_id)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.id)
    )
    return list(
        db.execute(
            select(Organization)
            .where(or_(Organization.owner_id == current_user.id, Organization.id.in_(project_orgs)))
            .order_by(Organization.created_at.desc())
        ).scalars()
    )


@router.post("", response_model=OrganizationRead, status_code=201)
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    organization = Organization(
        name=payload.name,
        slug=_unique_slug(db, Organization, payload.name),
        owner_id=current_user.id,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.post("/{organization_id}/projects", response_model=ProjectRead, status_code=201)
def create_project(
    organization_id: str,
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise NotFoundError("Organization not found.")
    if organization.owner_id != current_user.id:
        raise AuthorizationError("Only organization owners can create projects.")
    project = Project(
        organization_id=organization_id,
        name=payload.name,
        slug=_unique_project_slug(db, organization_id, payload.name),
        description=payload.description,
    )
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role=MemberRole.OWNER))
    db.add(
        RetryPolicy(
            project_id=project.id,
            name="default-exponential",
            strategy=RetryStrategy.EXPONENTIAL,
            max_attempts=3,
            delay_seconds=30,
            max_delay_seconds=1800,
        )
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("/{organization_id}/projects", response_model=list[ProjectRead])
def list_projects(
    organization_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Project]:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise NotFoundError("Organization not found.")
    if organization.owner_id == current_user.id:
        stmt = select(Project).where(Project.organization_id == organization_id)
    else:
        stmt = (
            select(Project)
            .join(ProjectMember)
            .where(Project.organization_id == organization_id, ProjectMember.user_id == current_user.id)
        )
    return list(db.execute(stmt.order_by(Project.created_at.desc())).scalars())


def _unique_project_slug(db: Session, organization_id: str, name: str) -> str:
    base = slugify(name)
    slug = base
    index = 2
    while db.execute(
        select(Project.id).where(Project.organization_id == organization_id, Project.slug == slug)
    ).scalar_one_or_none():
        slug = f"{base}-{index}"
        index += 1
    return slug


def _unique_slug(db: Session, model, name: str) -> str:
    base = slugify(name)
    slug = base
    index = 2
    while db.execute(select(model.id).where(model.slug == slug)).scalar_one_or_none():
        slug = f"{base}-{index}"
        index += 1
    return slug

