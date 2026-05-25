from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReviewBase(BaseModel):
    asin: str
    reviewer_name: Optional[str]
    rating: float
    title: Optional[str]
    body: str
    sentiment_score: float
    sentiment_label: str
    verified_purchase: Optional[str]
    review_date: Optional[str]

class ReviewOut(ReviewBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    asin: str
    title: str
    price: float
    original_price: float
    discount_percent: float
    rating: float
    review_count: int
    category: Optional[str]
    image_url: Optional[str]
    product_url: Optional[str]
    sentiment_score: float

class ProductOut(ProductBase):
    id: int
    brand_id: int

    class Config:
        from_attributes = True

class ProductWithReviews(ProductOut):
    reviews: List[ReviewOut] = []

    class Config:
        from_attributes = True


class BrandBase(BaseModel):
    name: str
    avg_price: float
    avg_discount: float
    avg_rating: float
    total_reviews: int
    sentiment_score: float

class BrandOut(BrandBase):
    id: int

    class Config:
        from_attributes = True

class BrandWithProducts(BrandOut):
    products: List[ProductOut] = []

    class Config:
        from_attributes = True


class BrandComparison(BaseModel):
    brand_name: str
    avg_price: float
    avg_discount: float
    avg_rating: float
    total_reviews: int
    sentiment_score: float
    top_pros: List[str]
    top_cons: List[str]


class InsightOut(BaseModel):
    id: int
    brand_name: str
    insight_type: str
    insight_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardOverview(BaseModel):
    total_brands: int
    total_products: int
    total_reviews: int
    avg_sentiment: float
    avg_price: float
    avg_discount: float