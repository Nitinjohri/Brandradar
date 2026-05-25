from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models

from ..Database import get_db
from .. import schemas

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=List[schemas.BrandOut])
def get_all_brands(db: Session = Depends(get_db)):
    return db.query(models.Brand).all()


@router.get("/overview", response_model=schemas.DashboardOverview)
def get_dashboard_overview(db: Session = Depends(get_db)):
    brands = db.query(models.Brand).all()
    products = db.query(models.Product).all()
    reviews = db.query(models.Review).all()

    if not brands:
        raise HTTPException(status_code=404, detail="No data found")

    return schemas.DashboardOverview(
        total_brands=len(brands),
        total_products=len(products),
        total_reviews=len(reviews),
        avg_sentiment=float(
            round(sum(b.sentiment_score for b in brands) / len(brands), 4)
        ),
        avg_price=float(
            round(sum(b.avg_price for b in brands) / len(brands), 2)
        ),
        avg_discount=float(
            round(sum(b.avg_discount for b in brands) / len(brands), 2)
        ),
    )


@router.get("/compare", response_model=List[schemas.BrandComparison])
def compare_brands(db: Session = Depends(get_db)):
    from ..agents.ollama import extract_themes

    brands = db.query(models.Brand).all()
    result = []

    for brand in brands:
        products = db.query(models.Product).filter(
            models.Product.brand_id == brand.id
        ).all()

        product_ids = [p.id for p in products]
        reviews = db.query(models.Review).filter(
            models.Review.product_id.in_(product_ids)
        ).all()

        positive_reviews = [str(r.body) for r in reviews if r.sentiment_label == "positive"]
        negative_reviews = [str(r.body) for r in reviews if r.sentiment_label == "negative"]

        pros = extract_themes(str(brand.name), positive_reviews, "positive")
        cons = extract_themes(str(brand.name), negative_reviews, "negative")

        result.append(schemas.BrandComparison(
            brand_name=str(brand.name),
            avg_price=float(brand.avg_price),
            avg_discount=float(brand.avg_discount),
            avg_rating=float(brand.avg_rating),
            total_reviews=int(brand.total_reviews),
            sentiment_score=float(brand.sentiment_score),
            top_pros=pros,
            top_cons=cons,
        ))

    return result


@router.get("/{brand_name}", response_model=schemas.BrandWithProducts)
def get_brand(brand_name: str, db: Session = Depends(get_db)):
    brand = db.query(models.Brand).filter(
        models.Brand.name.ilike(brand_name)
    ).first()

    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    return brand