from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.metrics import OverviewMetrics
from app.services.metrics import overview_metrics

router = APIRouter()


@router.get("/overview", response_model=OverviewMetrics)
def overview(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return overview_metrics(db)

