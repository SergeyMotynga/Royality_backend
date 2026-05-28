"""ORM-модель пользователя."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.post import Post
    from backend.app.models.post_comment import PostComment
    from backend.app.models.post_like import PostLike
    from backend.app.models.push_device_token import PushDeviceToken


class User(Base):
    """Пользователь социальной сети."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    liked_posts: Mapped[list["PostLike"]] = relationship(back_populates="user")
    comments: Mapped[list["PostComment"]] = relationship(back_populates="author")
    push_tokens: Mapped[list["PushDeviceToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
