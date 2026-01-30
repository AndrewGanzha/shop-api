from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    comment: str | None = Field(description="Комментарий к отзыву")
    grade: int = Field(..., le=5, gt=0)
    product_id: int = Field(...)

class Review(BaseModel):
    id: int = Field(...)
    user_id: int = Field(...)
    product_id: int
    comment: str | None = Field()
    comment_date: datetime | None = Field()
    grade: int
    product_id: int