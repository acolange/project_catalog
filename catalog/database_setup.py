from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """docstring for User."""
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String)

    @property
    def serialize(self):
        """Return object data in easily serialize format"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
        }


class Category(Base):
    """docstring for category."""
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    items = relationship("Item", backref="category")

    @property
    def serialize(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'items': [i.catSerialize for i in self.items]
        }


class Item(Base):
    """docstring for Item."""
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(String(10))
    picture = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))
    # category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'picture': self.picture,
            'category': self.category.name
        }

    @property
    def catSerialize(self):
        return {
            'ID': self.id,
            'Name': self.name,
            'Description': self.description,
            'Price': self.price,
            'Picture': self.picture
        }

engine = create_engine('sqlite:///sitecatalog.db')

Base.metadata.create_all(engine)
