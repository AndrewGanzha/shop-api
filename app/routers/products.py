from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException, status, Query
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.schemas.products import ProductCreate, Product as ProductSchema, ProductList
from sqlalchemy import select, func, update
from app.models import Product as ProductModel
from app.models.users import User as UserModel
from app.models.categories import Category as CategoryModel
from app.db_depends import get_async_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=ProductList)
async def get_all_products(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        category_id: int | None = Query(
            None, description="ID категории для фильтрации"),
        min_price: float | None = Query(
            None, ge=0, description="Минимальная цена товара"),
        max_price: float | None = Query(
            None, ge=0, description="Максимальная цена товара"),
        in_stock: bool | None = Query(
            None, description="true — только товары в наличии, false — только без остатка"),
        seller_id: int | None = Query(
            None, description="ID продавца для фильтрации"),
        created_at: date | None = Query(
            None, description="Дата создания товара в формате YYYY-MM-DD для фильтрации"),
        updated_at: date | None = Query(
            None, description="Дата последнего обновления товара в формате YYYY-MM-DD для фильтрации"),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Возвращает список всех активных товаров с поддержкой фильтров.
    """
    # Проверка логики min_price <= max_price
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price не может быть больше max_price",
        )

    # Формируем список фильтров
    filters = [ProductModel.is_active == True]

    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if min_price is not None:
        filters.append(ProductModel.price >= min_price)
    if max_price is not None:
        filters.append(ProductModel.price <= max_price)
    if in_stock is not None:
        filters.append(ProductModel.stock > 0 if in_stock else ProductModel.stock == 0)
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)
    if created_at is not None:
        filters.append(func.date(ProductModel.created_at) == created_at)
    if updated_at is not None:
        filters.append(func.date(ProductModel.updated_at) == updated_at)

    # Подсчёт общего количества с учётом фильтров
    total_stmt = select(func.count()).select_from(ProductModel).where(*filters)
    total = await db.scalar(total_stmt) or 0

    # Выборка товаров с фильтрами и пагинацией
    products_stmt = (
        select(ProductModel)
        .where(*filters)
        .order_by(ProductModel.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.scalars(products_stmt)).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.post("/", response_model=ProductSchema)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_user)):
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    result = await db.scalars(select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True))
    category = result.first()

    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    now = datetime.now(timezone.utc)
    product = ProductModel(
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url,
        stock=product.stock,
        category_id=product.category_id,
        seller_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product


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
        .values(**new_product.model_dump(), updated_at=datetime.now(timezone.utc))
    )
    await db.commit()
    await db.refresh(product)

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
