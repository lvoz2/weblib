from typing import Any, Optional, Sequence
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import mutable


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


class Item(Base):
    __tablename__ = "items"

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(255))
    description: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(1023))
    thumb_ext: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(10))
    thumb_mime: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(255))
    thumb_height: orm.Mapped[int] = orm.mapped_column(sqlalchemy.Integer())
    source_url: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(1023))
    source_name: orm.Mapped[str] = orm.mapped_column(sqlalchemy.String(64))
    saved_by: orm.Mapped[list["User"]] = orm.relationship(
        secondary=users_to_saved, back_populates="saved_items"
    )

    def __repr__(self) -> str:
        return (
            f"Item(id={self.id}, title={self.title}, description={self.description},"
            + f" thumb_ext={self.thumb_ext}, thumb_mime={self.thumb_mime},"
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
    platform_id: orm.Mapped[dict] = orm.mapped_column(
        mutable.MutableDict.as_mutable(sqlalchemy.JSON)
    )
    saved_items: orm.Mapped[list[Item]] = orm.relationship(
        secondary=users_to_saved, back_populates="saved_by"
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, login_platform={self.login_platform},"
            + f" platform_id={self.platform_id}, saved_items="
            + str(
                [f'"{item.title}" from {item.source_name}' for item in self.saved_items]
            )
        )


def setup_db(include_test: bool = False) -> None:
    Base.metadata.create_all(engine)
    if include_test:
        aus = Item(
            title="Australia",
            description="Australia, officially the Commonwealth of Australia, "
            + "is a country comprising the mainland of the Australian continent, "
            + "the island of Tasmania and numerous smaller islands. It has a "
            + "total area of 7,688,287 km2 (2,968,464 sq mi), making it the "
            + "sixth-largest country in the world and the largest in Oceania. "
            + "Australia is the world's flattest and driest inhabited continent. "
            + "It is a megadiverse country, and its size gives it a wide variety "
            + "of landscapes and climates including deserts in the interior and "
            + "tropical rainforests along the coast.",
            thumb_ext="svg",
            thumb_mime="image/svg+xml",
            thumb_height=100,
            source_url="https://en.wikipedia.org/wiki/Australia",
            source_name="Wikipedia",
        )
        with orm.Session(engine) as session:
            session.add(aus)
            session.commit()


def item_to_json(
    item: Item, is_saved: bool = False
) -> dict[str, str | bool | int | dict[str, str]]:
    return {
        "id": str(item.id),
        "title": item.title,
        "description": item.description,
        "thumb_ext": item.thumb_ext,
        "thumb_mime": item.thumb_mime,
        "thumb_height": item.thumb_height,
        "saved": is_saved,
        "source": {
            "url": item.source_url,
            "name": item.source_name,
        },
    }


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
            return item_to_json(item, is_saved)
        else:
            session.commit()
            return None


def get_or_create_user(
    email: str,
    platform: str,
    platform_id: dict[str, str],
    *args: Any,
    name: Optional[str] = None,
    username: Optional[str] = None,
) -> User:
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
            print(new_user)
            return new_user
        elif len(user) == 1:
            session.commit()
            print(user[0])
            return user[0]
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
            return [item_to_json(item, True) for item in user.saved_items]
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
