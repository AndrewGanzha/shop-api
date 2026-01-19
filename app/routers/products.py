from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.db_depends import get_db
from app.schemas import ProductCreate
from app.schemas import Product as ProductSchema
from sqlalchemy import select, update
from app.models import Product as ProductModel
from app.models.categories import Category as CategoryModel

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=List[ProductSchema])
async def get_all_products(db: Session = Depends(get_db)):
    stmt = select(ProductModel).where(ProductModel.is_active == True)
    products = db.scalars(stmt).all()

    return products


@router.post("/", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    stmt = select(CategoryModel).where(CategoryModel.id == product.category_id)
    category = db.scalars(stmt).first()

    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


@router.get("/category/{category_id}")
async def get_products_by_category(category_id: int):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    return {"message": f"Товары в категории {category_id} (заглушка)"}


@router.get("/{product_id}")
async def get_product(product_id: int):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    return {"message": f"Детали товара {product_id} (заглушка)"}


@router.put("/{product_id}")
async def update_product(product_id: int):
    """
    Обновляет товар по его ID.
    """
    return {"message": f"Товар {product_id} обновлён (заглушка)"}


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """
    Удаляет товар по его ID.
    """
    return {"message": f"Товар {product_id} удалён (заглушка)"}