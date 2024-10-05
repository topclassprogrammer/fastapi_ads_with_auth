import datetime
import uuid
from typing import Annotated

from config import TOKEN_TTL
from fastapi import Depends, Header, HTTPException
from models import Session, Token
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncSession:
    """Получение сессии"""
    async with Session() as session:
        return session


SessionDependency = Annotated[AsyncSession,
                              Depends(get_session, use_cache=True)]


async def get_token(
    x_token: Annotated[uuid.UUID, Header()], session: SessionDependency
) -> Token:
    """Получение токена"""
    token_query = select(Token).where(
        Token.token == x_token,
        Token.created_at >= func.now() - datetime.timedelta(
            seconds=int(TOKEN_TTL)))
    token = await session.scalar(token_query)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token


TokenDependency = Annotated[Token, Depends(get_token)]
