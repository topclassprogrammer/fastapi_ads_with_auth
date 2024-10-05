import datetime
import uuid

from config import PG_DSN
from data_types import ModelName
from sqlalchemy import (UUID, Boolean, CheckConstraint, Column, DateTime,
                        Float, ForeignKey, Integer, String, Table,
                        UniqueConstraint, func)
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

engine = create_async_engine(PG_DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    @property
    def id_dict(self):
        return {"id": self.id}


user_roles = Table("user_roles_relation", Base.metadata,
                   Column("user_id", ForeignKey("user.id"), index=True),
                   Column("role_id", ForeignKey("role.id"), index=True))

role_rights = Table("role_rights_relation", Base.metadata,
                    Column("role_id", ForeignKey("role.id"), index=True),
                    Column("right_id", ForeignKey("right.id"), index=True))


class Advertisement(Base):
    __tablename__ = 'advertisement'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(48), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User", lazy="joined",
                                        back_populates="advertisements")

    @property
    def dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id
        }


class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now())
    tokens: Mapped["Token"] = relationship(
        "Token", lazy="joined", back_populates="user",
        cascade="all, delete, delete-orphan")
    advertisements: Mapped[Advertisement] = relationship(
        "Advertisement", lazy="joined", back_populates="user",
        cascade="all, delete, delete-orphan")
    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary=user_roles, lazy="joined")

    @property
    def dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class Token(Base):
    __tablename__ = 'token'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[uuid.UUID] = mapped_column(
        UUID, server_default=func.gen_random_uuid(), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "user.id", ondelete="CASCADE"))
    user: Mapped[User] = relationship(
        User, lazy="joined", back_populates="tokens")

    @property
    def dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "created_at": self.created_at,
            "user_id": self.user_id
        }


class Role(Base):
    __tablename__ = 'role'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    rights: Mapped[list["Right"]] = relationship(
        "Right", secondary=role_rights, lazy="joined")


class Right(Base):
    __tablename__ = 'right'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    write: Mapped[bool] = mapped_column(Boolean, default=False)
    only_own: Mapped[bool] = mapped_column(Boolean, default=False)
    model: Mapped[ModelName] = mapped_column(String(32), nullable=False)

    __table_args__ = (
        UniqueConstraint("read", "write", "only_own", "model"),
        CheckConstraint("model in ('Advertisement', 'User')")
    )


ORM_OBJECT = Advertisement | User
ORM_CLS = type[Advertisement | User]
