from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


def paginate(db: Session, stmt: Select, *, limit: int, offset: int) -> dict:
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = list(db.execute(stmt.offset(offset).limit(limit)).scalars())
    return {"items": items, "total": total, "limit": limit, "offset": offset}

