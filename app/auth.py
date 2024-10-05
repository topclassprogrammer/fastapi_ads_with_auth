import bcrypt
from config import DEFAULT_ADMIN_ROLE
from fastapi import HTTPException
from models import ORM_OBJECT, Advertisement, Right, Role, Token, User
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession


def check_password(password: str, hashed_password: str) -> bool:
    password = password.encode()
    hashed_password = hashed_password.encode()
    return bcrypt.checkpw(password, hashed_password)


def hash_password(password: str) -> str:
    password = password.encode()
    password = bcrypt.hashpw(password, bcrypt.gensalt())
    return password.decode()


async def get_default_role(role_name: str, session: AsyncSession) -> Role:
    query = select(Role).where(Role.name == role_name)
    role = await session.scalar(query)
    return role


async def check_access_rights(
    session: AsyncSession,
    token: Token,
    model: ORM_OBJECT,
    write: bool,
    read: bool,
    owner_field: str = "user_id",
    raise_exception: bool = True,
) -> bool:
    """Проверка прав доступа над экземпляром модели"""

    # Проверяем есть ли у пользователя роль админа, и если есть,
    # то проверяем, что у него есть права над совершением действий
    # над запрашиваемым экземпляром моделью
    user_roles = token.user.roles
    for role in user_roles:
        if role.name == DEFAULT_ADMIN_ROLE:
            role_rights = role.rights
            for right in role_rights:
                if right.model == model.__class__.__name__:
                    return True

    # Получаем поле модели, по которому определяем принадлежность
    # экземпляра модели конкретному пользователю
    if isinstance(model, User):
        field = model.id
    elif isinstance(model, Advertisement):
        field = model.user_id
    else:
        field = 0

    where_args = [token.user_id == field,
                  Right.model == model.__class__.__name__]

    if write:
        where_args.append(Right.write == True)
    if read:
        where_args.append(Right.read == True)
    if (hasattr(model, owner_field)) and \
            getattr(model, owner_field) != token.user_id:
        where_args.append(Right.only_own == False)
    right_query = (
        select(func.count(distinct(Right.id)))
        .join(Role, User.roles)
        .join(Right, Role.rights)
        .where(*where_args)
    )
    rights_count = await session.scalar(right_query)
    if not rights_count and raise_exception:
        raise HTTPException(403, detail="Access denied")
    return rights_count > 0
