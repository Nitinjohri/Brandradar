from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.Database import engine
from backend import models
from backend.routers import brands, products, reviews, insights

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Luggage Intelligence API",
    description=(
        "Competitive intelligence dashboard for luggage brands on "
        "Amazon India"
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brands.router)
app.include_router(products.router)
app.include_router(reviews.router)
app.include_router(insights.router)


@app.get("/")
def root():
    return {
        "message": "Luggage Intelligence API is running",
        "docs": "/docs",
        "endpoints": [
            "/brands",
            "/brands/overview",
            "/brands/compare",
            "/products",
            "/reviews",
            "/insights/market",
            "/insights/brand/{brand_name}"
        ]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
