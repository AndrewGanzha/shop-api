from typing import List

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db_depends import get_async_db
from app.models import Review, Product
from app.models.users import User as UserModel
from app.schemas import Review as ReviewSchema
from app.schemas.reviews import ReviewCreate

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)

@router.get("/", response_model=List[ReviewSchema])
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(Review).where(Review.is_active == True))
    reviews = result.all()

    return reviews

@router.get("/{products_id}", response_model=List[ReviewSchema])
async def get_review(products_id: int, db: AsyncSession = Depends(get_async_db)):
    product = await db.scalar(select(Product).where(Product.id == products_id))

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = await db.scalars(select(Review).where(Review.is_active == True, Review.product_id == products_id))

    return reviews

@router.post("/", response_model=ReviewSchema)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    product = await db.scalar(select(Product).where(Product.id == payload.product_id, Product.is_active == True))

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_review = await db.scalar(select(Review).where(Review.user_id == current_user.id, Review.is_active == True))

    if old_review:
        raise HTTPException(status_code=403, detail="Already have review")

    review = Review(
        user_id = current_user.id,
        product_id = payload.product_id,
        comment = payload.comment,
        grade = payload.grade,
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    return review

@router.delete("/{review_id}")
async def delete_review(review_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    review = await db.scalar(select(Review).where(Review.is_active == True, Review.id == review_id))

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if not review.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    await db.delete(review)
    await db.commit()
    return { "message": f"Review {review_id} deleted" }