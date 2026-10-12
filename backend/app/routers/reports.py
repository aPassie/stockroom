from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from ..db import get_db
from ..models import Product, StockMovement
from ..schemas import CategoryCount, MovementOut, StatsOut
from .products import movement_out

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    totals = db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            func.coalesce(func.sum(Product.quantity * Product.unit_price), 0),
            func.coalesce(func.sum(case((Product.quantity <= Product.reorder_level, 1), else_=0)), 0),
            func.coalesce(func.sum(case((Product.quantity == 0, 1), else_=0)), 0),
        )
    ).one()
    categories = db.execute(
        select(Product.category, func.count(Product.id), func.coalesce(func.sum(Product.quantity), 0))
        .group_by(Product.category)
        .order_by(Product.category)
    ).all()
    return StatsOut(
        products=totals[0],
        units=totals[1],
        inventory_value=Decimal(totals[2]).quantize(Decimal("0.01")),
        low_stock=totals[3],
        out_of_stock=totals[4],
        categories=[CategoryCount(category=c, products=p, units=u) for c, p, u in categories],
    )


@router.get("/movements", response_model=list[MovementOut])
def recent_movements(limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)):
    movements = db.scalars(
        select(StockMovement).options(joinedload(StockMovement.product)).order_by(StockMovement.id.desc()).limit(limit)
    )
    return [movement_out(m) for m in movements]
