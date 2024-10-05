import auth
import fastapi
import schema
from crud import add_item, delete_item, get_item, search_items
from dependencies import SessionDependency, TokenDependency
from fastapi import HTTPException
from lifespan import lifespan
from models import Advertisement, Token, User
from sqlalchemy import select

app = fastapi.FastAPI(
    title="Сервис объявлений",
    description="Получение/создание/обновление/удаление "
                "пользователей и объявлений",
    version="0.1",
    lifespan=lifespan,
)


@app.post("/user", response_model=schema.CreateUserResponse)
async def create_user(user_data: schema.CreateUserRequest,
                      session: SessionDependency):
    """Создание пользователя"""
    user = User(**user_data.dict())
    user.password = auth.hash_password(user_data.password)
    role = await auth.get_default_role("user", session)
    user.roles = [role]
    user = await add_item(user, session)
    return user.id_dict


@app.get("/user/{user_id}", response_model=schema.GetUserResponse)
async def get_user(user_id: int, session: SessionDependency):
    """Получение пользователя по id"""
    user = await get_item(user_id, User, session)
    return user.dict


@app.patch("/user/{user_id}", response_model=schema.UpdateUserResponse)
async def update_user(
        user_id: int,
        update_data: schema.UpdateUserRequest,
        session: SessionDependency,
        token: TokenDependency,
):
    """Обновление пользователя"""
    user = await get_item(user_id, User, session)
    await auth.check_access_rights(session, token, user,
                                   write=True, read=False)
    update_data = update_data.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(user, k, v)
    await add_item(user, session)
    return user.id_dict


@app.delete("/user/{user_id}", response_model=schema.DeleteUserResponse)
async def delete_user(user_id: int, session: SessionDependency,
                      token: TokenDependency):
    """Удаление пользователя"""
    user = await get_item(user_id, User, session)
    await auth.check_access_rights(session, token, user,
                                   write=True, read=False)
    await delete_item(user_id, User, session)
    return {"status": "success"}


@app.post("/login", response_model=schema.LoginResponse)
async def login(login_data: schema.LoginRequest, session: SessionDependency):
    """Аутентификация пользователя"""
    user_query = select(User).where(User.name == login_data.name)
    user = await session.scalar(user_query)
    if not user or not auth.check_password(login_data.password, user.password):
        raise HTTPException(status_code=401, detail="User or password is "
                                                    "incorrect")
    token = Token(user_id=user.id)
    await add_item(token, session)
    return {"token": token.token}


@app.get("/advertisement")
async def get_advertisement_from_qs(
        session: SessionDependency, request: fastapi.Request
):
    """Получение объявления из query string"""
    query_params = request.query_params
    query_params_str = str(query_params)
    # Ограничение: поиск возможен только по одному параметру
    if "&" in query_params_str:
        raise HTTPException(
            status_code=400, detail="Too many parameters in query string"
        )
    if "=" not in query_params_str:
        raise HTTPException(status_code=400, detail="Invalid query parameters")
    query_param = query_params_str.split("=")
    field = query_param[0]
    value = query_param[1]
    if field not in Advertisement.__dict__.keys():
        raise HTTPException(status_code=400,
                            detail=f"Field {field} does not exist")
    items = await search_items(session, Advertisement, field, value)
    return [item.dict for item in items]


@app.get(
    "/advertisement/{advertisement_id}",
    response_model=schema.GetAdvertisementResponse
)
async def get_advertisement(advertisement_id: int, session: SessionDependency):
    """Получение объявления по id"""
    item = await get_item(advertisement_id, Advertisement, session)
    return item.dict


@app.post("/advertisement",
          response_model=schema.CreateAdvertisementResponse)
async def create_advertisement(
        advertisement_json: schema.CreateAdvertisementRequest,
        session: SessionDependency,
        token: TokenDependency,
):
    """Создание объявления"""
    item = Advertisement(**advertisement_json.dict(), user_id=token.user_id)
    await add_item(item, session)
    return item.id_dict


@app.patch(
    "/advertisement/{advertisement_id}",
    response_model=schema.UpdateAdvertisementResponse,
)
async def update_advertisement(
        advertisement_id: int,
        advertisement_json: schema.UpdateAdvertisementRequest,
        session: SessionDependency,
        token: TokenDependency,
):
    """Обновление объявления"""
    item = await get_item(advertisement_id, Advertisement, session)
    await auth.check_access_rights(session, token, item,
                                   write=True, read=False)
    item_update = advertisement_json.dict(exclude_unset=True)
    for k, v in item_update.items():
        setattr(item, k, v)
    await add_item(item, session)
    return item.id_dict


@app.delete(
    "/advertisement/{advertisement_id}",
    response_model=schema.DeleteAdvertisementResponse,
)
async def delete_advertisement(
        advertisement_id: int, session: SessionDependency,
        token: TokenDependency
):
    """Удаление объявления"""
    item = await get_item(advertisement_id, Advertisement, session)
    await auth.check_access_rights(session, token, item,
                                   write=True, read=False)
    await delete_item(advertisement_id, Advertisement, session)
    return {"status": "success"}
