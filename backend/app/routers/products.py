from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Product, StockMovement
from ..schemas import MovementCreate, MovementOut, ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


def get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


def movement_out(movement: StockMovement) -> MovementOut:
    return MovementOut(
        id=movement.id,
        product_id=movement.product_id,
        product_name=movement.product.name,
        change=movement.change,
        reason=movement.reason,
        note=movement.note,
        created_at=movement.created_at,
    )


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = None,
    category: str | None = None,
    low_stock: bool = False,
    db: Session = Depends(get_db),
):
    query = select(Product).order_by(Product.name)
    if q:
        pattern = f"%{q.lower()}%"
        query = query.where(or_(func.lower(Product.name).like(pattern), func.lower(Product.sku).like(pattern)))
    if category:
        query = query.where(Product.category == category)
    if low_stock:
        query = query.where(Product.quantity <= Product.reorder_level)
    return db.scalars(query).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_or_404(product_id, db)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump(exclude={"sku"}), sku=payload.sku.upper())
    if payload.quantity:
        product.movements.append(StockMovement(change=payload.quantity, reason="RESTOCK", note="Opening stock"))
    db.add(product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"SKU {product.sku} already exists")
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db.delete(get_product_or_404(product_id, db))
    db.commit()


@router.get("/{product_id}/movements", response_model=list[MovementOut])
def list_product_movements(product_id: int, db: Session = Depends(get_db)):
    product = get_product_or_404(product_id, db)
    movements = db.scalars(
        select(StockMovement).where(StockMovement.product_id == product.id).order_by(StockMovement.id.desc())
    )
    return [movement_out(m) for m in movements]


@router.post("/{product_id}/movements", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
def record_movement(product_id: int, payload: MovementCreate, db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.id == product_id).with_for_update())
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    if product.quantity + payload.change < 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Only {product.quantity} units of {product.sku} in stock"
        )
    product.quantity += payload.change
    movement = StockMovement(product=product, **payload.model_dump())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement_out(movement)
