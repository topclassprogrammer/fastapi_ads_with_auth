import datetime
import re

from fastapi import HTTPException
from models import ORM_CLS, ORM_OBJECT, Advertisement
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


async def add_item(item: ORM_OBJECT, session: AsyncSession) -> ORM_OBJECT:
    """Добавление или изменение объекта в БД"""
    session.add(item)
    try:
        await session.commit()
    except IntegrityError as err:
        if err.orig.pgcode == "23505":
            raise HTTPException(status_code=409, detail="Item already exists")
        raise err
    return item


async def get_item(
    item_id: int, orm_class: ORM_CLS, session: AsyncSession
) -> ORM_OBJECT:
    """Получение объекта из БД"""
    item = await session.get(orm_class, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


async def delete_item(item_id: int, orm_class: ORM_CLS, session: AsyncSession)\
        -> None:
    """Удаление объекта в БД"""
    item = await get_item(item_id, orm_class, session)
    await session.delete(item)
    await session.commit()


async def search_items(
    session: AsyncSession, orm_class: ORM_CLS, field, value
) -> dict | list[dict]:
    """Получение объекта из БД по условию"""
    orm_class_field = getattr(orm_class, field)
    annotations = orm_class.__dict__["__annotations__"]
    # Словарь с ключами из названий полей модели и
    # значениями аннотируемых полей модели
    mapped_dict = {}
    for k, v in annotations.items():
        v = str(v).split("Mapped")[1].strip("[]")
        mapped_dict.setdefault(k, v)
    # Получаем тип данных по которому мы будем формировать условие
    # для query-выражения к БД
    type_field = mapped_dict[field]
    if type_field == "int":
        condition = orm_class_field == int(value)
    elif type_field == "float":
        condition = orm_class_field == float(value)
    elif type_field == "str":
        condition = orm_class_field.ilike(f"%{value}%")
    elif type_field == "datetime.datetime":
        match = re.match(r"\d{4}-\d{2}-\d{2}", value)
        if match:
            match = match[0]
            match_datetime = datetime.datetime.fromisoformat(match)
            match_date = match_datetime.date()
            condition = func.date(Advertisement.created_at) == match_date
        else:
            raise HTTPException(status_code=400, detail="Invalid date")
    query = await session.scalars(select(orm_class).where(condition))
    res_list = query.unique().all()
    if not res_list:
        raise HTTPException(status_code=404,
                            detail=f"{value} not found in {field}")
    return res_list
