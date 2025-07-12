import sqlalchemy
from sqlalchemy import orm
from typing import Optional


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
    saved_items: orm.Mapped[list[Item]] = orm.relationship(
        secondary=users_to_saved, back_populates="saved_by"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, saved_items=" + str(
            [f'"{item.title}" from {item.source_name}' for item in self.saved_items]
        )


def get_item(
    id: int, user_id: Optional[int] = None
) -> Optional[dict[str, str | bool | int | dict[str, str]]]:
    with orm.Session(engine) as session:
        item: Optional[Item] = session.get(Item, id)
        if item is not None:
            is_saved = False
            if user_id is not None:
                user: Optional[User] = session.get(User, user_id)
                if user is not None:
                    is_saved = item.saved_by.index(user) >= 0

            session.commit()
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
        else:
            session.commit()
            return None
