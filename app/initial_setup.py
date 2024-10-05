import auth
from config import DEFAULT_ADMIN_ROLE, DEFAULT_USER_ROLE
from models import Advertisement, Right, Role, Token, User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_default_roles(session: AsyncSession) -> None:
    """Установка дефолтных ролей и прав"""
    default_roles_rights = {DEFAULT_ADMIN_ROLE: True, DEFAULT_USER_ROLE: False}
    rights = []
    for default_role, default_right in default_roles_rights.items():
        for model in (User, Advertisement):
            right = Right(
                read=True, write=default_right, only_own=True,
                model=model.__name__)
            rights.append(right)
        role = Role(name=default_role, rights=[*rights])
        session.add_all([role, *rights])
        rights = []
    await session.commit()


async def create_default_users(session: AsyncSession) -> None:
    """Установка дефолтных пользователей"""
    default_user_creds = [
        ("admin", "password", DEFAULT_ADMIN_ROLE),
        ("user", "password", DEFAULT_USER_ROLE),
    ]
    for el in default_user_creds:
        user = User(
            name=el[0],
            password=auth.hash_password(el[1]),
            roles=[await auth.get_default_role(el[2], session)],
        )
        await _save_obj(user, session)
        token = Token(user_id=user.id)
        await _save_obj(token, session)


async def _save_obj(obj: User | Token, session: AsyncSession) -> None:
    """Добавление объекта в сессию и коммит"""
    session.add(obj)
    await session.commit()
