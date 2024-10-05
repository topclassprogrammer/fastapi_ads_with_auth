from contextlib import asynccontextmanager

from fastapi import FastAPI
from initial_setup import create_default_roles, create_default_users
from models import Base, Session, engine
from sqlalchemy.exc import IntegrityError


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with Session() as session:
        try:
            await create_default_roles(session)
            await create_default_users(session)
        except IntegrityError:
            pass
    yield
    await engine.dispose()
