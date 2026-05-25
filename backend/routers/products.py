from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..Database import get_db
from .. import models,schemas

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[schemas.ProductOut])
def get_products(
    brand: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    if brand:
        brand_obj = db.query(models.Brand).filter(
            models.Brand.name.ilike(brand)
        ).first()
        if brand_obj:
            query = query.filter(models.Product.brand_id == brand_obj.id)

    if min_rating:
        query = query.filter(models.Product.rating >= min_rating)

    if min_price:
        query = query.filter(models.Product.price >= min_price)

    if max_price:
        query = query.filter(models.Product.price <= max_price)

    if category:
        query = query.filter(models.Product.category.ilike(f"%{category}%"))

    return query.all()


@router.get("/{product_id}", response_model=schemas.ProductWithReviews)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product