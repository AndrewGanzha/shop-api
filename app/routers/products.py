from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_depends import get_db
from app.schemas import ProductCreate
from app.schemas import Product as ProductSchema
from sqlalchemy import select, update
from app.models import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.db_depends import get_async_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=List[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(ProductModel).where(ProductModel.is_active == True))
    products = result.all()

    return products


@router.post("/", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True))
    category = result.first()

    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.get("/category/{category_id}")
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    result_category = await db.scalars(select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True))
    category = result_category.first()

    if category is None:
        raise HTTPException(status_code=400, detail="Category not found or inactive")

    result_products = await db.scalars(select(ProductModel).where(ProductModel.category_id == category_id))
    products = result_products.all()

    return products


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True))
    product = result.first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    )
    category = category_result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactive")

    return product


@router.put("/{product_id}")
async def update_product(product_id: int, new_product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id))
    product = result.first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    result_category = await db.scalars(select(CategoryModel).where(CategoryModel.id == new_product.category_id))
    category = result_category.first()

    if category is None:
        raise HTTPException(status_code=400, detail="Category not found or inactive")


    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**new_product.model_dump())
    )
    await db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id))
    product = result.first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(is_active=False))
    await db.commit()

    return {"status": "success", "message": "Product marked as inactive"}