from sqlalchemy import Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from datetime import datetime
from backend.Database import Base
from typing import List, Optional


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
        name: Mapped[str] = mapped_column(String, unique=True, index=True)
        avg_price: Mapped[float] = mapped_column(Float, default=0.0)
        avg_discount: Mapped[float] = mapped_column(Float, default=0.0)
        avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
        total_reviews: Mapped[int] = mapped_column(Integer, default=0)
        sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
        created_at: Mapped[datetime] = mapped_column(
            DateTime, default=datetime.utcnow
        )

    products: Mapped[List["Product"]] = relationship(back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"))
    asin: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    original_price: Mapped[float] = mapped_column(Float)
    discount_percent: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float)
    review_count: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String)
        image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        product_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
        created_at: Mapped[datetime] = mapped_column(
            DateTime, default=datetime.utcnow
        )

    brand: Mapped["Brand"] = relationship(back_populates="products")
    reviews: Mapped[List["Review"]] = relationship(back_populates="product")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    asin: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    reviewer_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rating: Mapped[float] = mapped_column(Float)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    body: Mapped[str] = mapped_column(Text)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_label: Mapped[str] = mapped_column(String, default="neutral")
    verified_purchase: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    review_date: Mapped[Optional[str]] = mapped_column(String, nullable=True)
        created_at: Mapped[datetime] = mapped_column(
            DateTime, default=datetime.utcnow
        )

    product: Mapped["Product"] = relationship(back_populates="reviews")


class AgentInsight(Base):
    __tablename__ = "agent_insights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    insight_type: Mapped[str] = mapped_column(String)
    insight_text: Mapped[str] = mapped_column(Text)
        created_at: Mapped[datetime] = mapped_column(
            DateTime, default=datetime.utcnow
        )

