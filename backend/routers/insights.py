from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..Database import get_db
from .. import models, schemas
from ..agents.ollama import (
    generate_brand_insights,
    generate_market_insights,
    extract_themes
)

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/market", response_model=List[schemas.InsightOut])
def get_market_insights(db: Session = Depends(get_db)):
    existing = db.query(models.AgentInsight).filter(
        models.AgentInsight.insight_type == "market"
    ).all()

    if existing:
        return existing

    brands = db.query(models.Brand).all()
    brands_summary = [
        {
            "name": b.name,
            "avg_price": b.avg_price,
            "avg_discount": b.avg_discount,
            "avg_rating": b.avg_rating,
            "sentiment_score": b.sentiment_score
        }
        for b in brands
    ]

    insights = generate_market_insights(brands_summary)

    saved = []
    for item in insights:
        brand_name = item.get("brand", "Market")
        insight_text = item.get("insight", str(item))

        insight = models.AgentInsight(
            brand_name=brand_name,
            insight_type="market",
            insight_text=insight_text
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        saved.append(insight)

    return saved


@router.get("/brand/{brand_name}", response_model=List[schemas.InsightOut])
def get_brand_insights(brand_name: str, db: Session = Depends(get_db)):
    existing = db.query(models.AgentInsight).filter(
        models.AgentInsight.brand_name.ilike(brand_name)
    ).all()

    if existing:
        return existing

    brand = db.query(models.Brand).filter(
        models.Brand.name.ilike(brand_name)
    ).first()

    if not brand:
        return []

    product_ids = [p.id for p in brand.products]
    reviews = db.query(models.Review).filter(
        models.Review.product_id.in_(product_ids)
    ).all()

    positive = [r.body for r in reviews if r.sentiment_label == "positive"]
    negative = [r.body for r in reviews if r.sentiment_label == "negative"]

    pros = extract_themes(brand.name, positive, "positive")
    cons = extract_themes(brand.name, negative, "negative")

    insights = generate_brand_insights(
        brand_name=brand.name,
        avg_price=brand.avg_price,
        avg_discount=brand.avg_discount,
        avg_rating=brand.avg_rating,
        sentiment_score=brand.sentiment_score,
        top_complaints=cons,
        top_praises=pros
    )

    saved = []
    for text in insights:
        insight = models.AgentInsight(
            brand_name=brand.name,
            insight_type="brand",
            insight_text=str(text)
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        saved.append(insight)

    return saved


@router.delete("/refresh")
def refresh_insights(db: Session = Depends(get_db)):
    db.query(models.AgentInsight).delete()
    db.commit()
    return {"message": "All insights cleared. Call /market or /brand to regenerate."}