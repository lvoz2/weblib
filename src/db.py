import datetime
from typing import Any, Optional, Sequence

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import mutable, associationproxy

engine = sqlalchemy.create_engine("sqlite:///server.db")


# engine = sqlalchemy.create_engine("sqlite:///server.db", echo=True)
class Base(orm.DeclarativeBase):
    pass


users_to_saved = sqlalchemy.Table(
    "users_to_saved",
    Base.metadata,
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id"), primary_key=True),
    sqlalchemy.Column("item_id", sqlalchemy.ForeignKey("items.id"), primary_key=True),
)


class UserToRecentlyViewed(Base):
    __tablename__ = "users_to_recent_view"

    user_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), primary_key=True
    )
    item_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("items.id"), primary_key=True
    )
    user: orm.Mapped["User"] = orm.relationship(
        back_populates="user_recent_viewed_assoc"
    )
    item: orm.Mapped["Item"] = orm.relationship()
    time_inserted: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer())

    def __repr__(self) -> str:
        return (
            f"UserToRecentlyViewed(user_id={self.user_id}, item_id={self.item_id},"
            + f" time_inserted={self.time_inserted})"
        )


class UserToRecentlySearched(Base):
    __tablename__ = "users_to_recent_search"

    user_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("users.id"), primary_key=True
    )
    item_id: orm.Mapped[int] = orm.mapped_column(
        sqlalchemy.ForeignKey("items.id"), primary_key=True
    )
    user: orm.Mapped["User"] = orm.relationship(
        back_populates="user_recent_search_assoc"
    )
    item: orm.Mapped["Item"] = orm.relationship()
    time_inserted: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer())

    def __repr__(self) -> str:
        return (
            f"UserToRecentlySearched(user_id={self.user_id}, item_id={self.item_id},"
            + f" time_inserted={self.time_inserted})"
        )


class Item(Base):
    __tablename__ = "items"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(255))
    description: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(1023))
    thumb_url: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(10))
    thumb_mime: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(255))
    thumb_height: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer())
    source_url: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(1023))
    source_name: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(64))
    source_id: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(16))
    saved_by: orm.Mapped[list["User"]] = orm.relationship(
        secondary=users_to_saved, back_populates="saved_items"
    )

    def to_dict(
        self, is_saved: bool = False
    ) -> dict[str, str | bool | int | dict[str, str]]:
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "thumb_url": self.thumb_url,
            "thumb_mime": self.thumb_mime,
            "thumb_height": self.thumb_height,
            "saved": is_saved,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "source_id": self.source_id,
        }

    def __repr__(self) -> str:
        return (
            f"Item(id={self.id}, title={self.title}, description={self.description},"
            + f" thumb_url={self.thumb_url}, thumb_mime={self.thumb_mime},"
            + f" thumb_height={self.thumb_height}, source_url={self.source_url},"
            + f" source_name={self.source_name})"
        )


class User(Base):
    __tablename__ = "users"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    email: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(254))
    name: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(254))
    username: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(254))
    login_platform: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(16))
    platform_id: orm.Mapped[dict[str, Any]] = orm.mapped_column(
        mutable.MutableDict.as_mutable(sqlalchemy.JSON)
    )
    saved_items: orm.Mapped[list[Item]] = orm.relationship(
        secondary=users_to_saved, back_populates="saved_by"
    )
    recently_viewed: associationproxy.AssociationProxy[list[Item]] = (
        associationproxy.association_proxy(
            "user_recent_viewed_assoc",
            "item",
        )
    )
    recently_searched: associationproxy.AssociationProxy[list[Item]] = (
        associationproxy.association_proxy(
            "user_recent_search_assoc",
            "item",
        )
    )

    user_recent_search_assoc: orm.Mapped[list[UserToRecentlySearched]] = (
        orm.relationship(
            back_populates="user",
            cascade="all, delete-orphan",
        )
    )
    user_recent_viewed_assoc: orm.Mapped[list[UserToRecentlyViewed]] = orm.relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    recent_max_len: int = 20

    def to_dict(self, include_saved: bool = False) -> dict[
        str,
        int | str | dict[str, Any] | list[dict[str, str | bool | int | dict[str, str]]],
    ]:
        if include_saved:
            return {
                "id": self.id,
                "email": self.email,
                "name": self.name,
                "username": self.username,
                "login_platform": self.login_platform,
                "platform_id": self.platform_id,
                "saved_items": [item.to_dict() for item in self.saved_items],
            }
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "username": self.username,
            "login_platform": self.login_platform,
            "platform_id": self.platform_id,
        }

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, login_platform={self.login_platform},"
            + f" platform_id={self.platform_id}, saved_items="
            + str(
                [f'"{item.title}" from {item.source_name}' for item in self.saved_items]
            )
        )


def get_recently_viewed(
    user_id: Optional[int],
) -> list[dict[str, str | bool | int | dict[str, str]]]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        if user is None:
            return []
        data: list[UserToRecentlyViewed] = sorted(
            user.user_recent_viewed_assoc,
            key=lambda assoc: assoc.time_inserted,
            reverse=True,
        )[: user.recent_max_len]
        return [assoc.item.to_dict(assoc.item in user.saved_items) for assoc in data]


def get_recently_searched(
    user_id: Optional[int],
) -> list[dict[str, str | bool | int | dict[str, str]]]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        if user is None:
            return []
        data: list[UserToRecentlySearched] = sorted(
            user.user_recent_search_assoc,
            key=lambda assoc: assoc.time_inserted,
            reverse=True,
        )[: user.recent_max_len]
        return [assoc.item.to_dict(assoc.item in user.saved_items) for assoc in data]


def append_to_recently_viewed(user_id: int, item_id: int) -> Optional[str]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        if user is None:
            return "user_id not valid"
        item: Optional[Item] = session.get(Item, item_id)
        if item is None:
            return "item_id not valid"
        time: int = int(
            datetime.datetime.now().replace(tzinfo=datetime.timezone.utc).timestamp()
            * 1000000
        )
        item_assoc: UserToRecentlyViewed = UserToRecentlyViewed(
            user=user, item=item, time_inserted=time
        )
        if (
            temp_assoc := session.get(UserToRecentlyViewed, (user_id, item_id))
        ) is not None:
            item_assoc = temp_assoc
            item_assoc.time_inserted = time
        else:
            item_assoc.item = item
            user.user_recent_viewed_assoc.append(item_assoc)
        user.user_recent_viewed_assoc = sorted(
            user.user_recent_viewed_assoc,
            key=lambda assoc: assoc.time_inserted,
            reverse=True,
        )[: user.recent_max_len]
        session.commit()
        return None


def append_to_recently_searched(user_id: int, item_id: int) -> Optional[str]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        if user is None:
            return "user_id not valid"
        item: Optional[Item] = session.get(Item, item_id)
        if item is None:
            return "item_id not valid"
        time: int = int(
            datetime.datetime.now().replace(tzinfo=datetime.timezone.utc).timestamp()
            * 1000000
        )
        item_assoc: UserToRecentlySearched = UserToRecentlySearched(
            user=user, item=item, time_inserted=time
        )
        if (
            temp_assoc := session.get(UserToRecentlySearched, (user_id, item_id))
        ) is not None:
            item_assoc = temp_assoc
            item_assoc.time_inserted = time
        else:
            item_assoc.item = item
            user.user_recent_search_assoc.append(item_assoc)
        user.user_recent_search_assoc = sorted(
            user.user_recent_search_assoc,
            key=lambda assoc: assoc.time_inserted,
            reverse=True,
        )[: user.recent_max_len]
        session.commit()
        return None


def setup_db() -> None:
    Base.metadata.create_all(engine)


def get_item(
    item_id: int, user_id: Optional[int] = None
) -> Optional[dict[str, str | bool | int | dict[str, str]]]:
    with orm.Session(engine) as session:
        item: Optional[Item] = session.get(Item, item_id)
        if item is not None:
            is_saved = False
            if user_id is not None:
                user: Optional[User] = session.get(User, user_id)
                if user is not None:
                    is_saved = user in item.saved_by
            session.commit()
            return item.to_dict(is_saved)
        else:
            session.commit()
            return None


def get_item_by_source(
    source_name: str,
    source_id: str,
    user_id: Optional[int] = None,
    add_to_recent_search: bool = False,
) -> Optional[dict[str, str | bool | int | dict[str, str]]]:
    with orm.Session(engine) as session:
        item: Sequence[Item] = session.scalars(
            sqlalchemy.select(Item)
            .where(Item.source_name == source_name)
            .where(Item.source_id == source_id)
        ).all()
        if len(item) == 0:
            session.commit()
            return None
        elif len(item) == 1:
            is_saved = False
            if user_id is not None:
                user: Optional[User] = session.get(User, user_id)
                if user is not None:
                    is_saved = user in item[0].saved_by
                    if add_to_recent_search:
                        append_to_recently_searched(user_id, item[0].id)
            session.commit()
            return item[0].to_dict(is_saved)
        else:
            session.commit()
            raise ValueError(
                f"Too many items found from {source_name} with source_id {source_id}"
            )


def create_item(
    item_data: dict[str, str | bool | int | dict[str, str]],
    user_id: Optional[int] = None,
    add_to_recent_search: bool = False,
) -> dict[str, str | bool | int | dict[str, str]]:
    with orm.Session(engine) as session:
        item: Item = Item(**item_data)
        session.add(item)
        session.commit()
        is_saved = False
        if user_id is not None:
            user: Optional[User] = session.get(User, user_id)
            if user is not None:
                is_saved = user in item.saved_by
                if add_to_recent_search:
                    append_to_recently_searched(user_id, item.id)
        return item.to_dict(is_saved)


def get_or_create_user(
    email: str,
    platform: str,
    platform_id: dict[str, str],
    *,
    name: Optional[str] = None,
    username: Optional[str] = None,
) -> dict[
    str,
    int | str | dict[str, Any] | list[dict[str, str | bool | int | dict[str, str]]],
]:
    with orm.Session(engine) as session:
        user: Sequence[User] = session.scalars(
            sqlalchemy.select(User)
            .where(User.login_platform == platform)
            .where(User.platform_id == platform_id)
        ).all()
        if len(user) == 0:
            # No user, need to create one
            new_user: User = User(
                email=email,
                login_platform=platform,
                platform_id=platform_id,
                name=name,
                username=username,
            )
            session.add(new_user)
            session.commit()
            return new_user.to_dict()
        elif len(user) == 1:
            session.commit()
            return user[0].to_dict()
        else:
            raise ValueError("Multiple users found with identical platform_id")


def get_saved_items(
    user_id: int,
) -> Optional[list[dict[str, str | bool | int | dict[str, str]]]]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        if user is not None:
            if len(user.saved_items) == 0:
                return None
            return [item.to_dict(True) for item in user.saved_items]
        raise ValueError(f"No user with id {user_id} found")


def save_item(item_id: int, user_id: int) -> Optional[str]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        item: Optional[Item] = session.get(Item, item_id)
        if user is None:
            return f'User with id "{user_id}" does not exist'
        if item is None:
            return f'Item with id "{item_id}" does not exist'
        user.saved_items.append(item)
        session.commit()
        return None


def unsave_item(item_id: int, user_id: int) -> Optional[str]:
    with orm.Session(engine) as session:
        user: Optional[User] = session.get(User, user_id)
        item: Optional[Item] = session.get(Item, item_id)
        if user is None:
            return f'User with id "{user_id}" does not exist'
        if item is None:
            return f'Item with id "{item_id}" does not exist'
        try:
            user.saved_items.remove(item)
        except ValueError:
            pass
        session.commit()
        return None


if __name__ == "__main__":
    pass
