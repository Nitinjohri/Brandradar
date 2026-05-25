from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..Database import get_db
from .. import models, schemas

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/", response_model=List[schemas.ReviewOut])
def get_reviews(
    product_id: Optional[int] = Query(None),
    sentiment: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Review)

    if product_id:
        query = query.filter(models.Review.product_id == product_id)

    if sentiment:
        query = query.filter(models.Review.sentiment_label == sentiment)

    if min_rating:
        query = query.filter(models.Review.rating >= min_rating)

    return query.limit(100).all()


@router.get("/brand/{brand_name}", response_model=List[schemas.ReviewOut])
def get_reviews_by_brand(
    brand_name: str,
    sentiment: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    brand = db.query(models.Brand).filter(
        models.Brand.name.ilike(brand_name)
    ).first()

    if not brand:
        return []

    product_ids = [p.id for p in brand.products]
    query = db.query(models.Review).filter(
        models.Review.product_id.in_(product_ids)
    )

    if sentiment:
        query = query.filter(models.Review.sentiment_label == sentiment)

    return query.limit(200).all()
