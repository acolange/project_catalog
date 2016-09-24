from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item

engine = create_engine('sqlite:///sitecatalog.db')
Base.metadata.bind = engine

DBSession = session(bind=engine)
sess = DBSession()

cat1 = Category(name='Baseball',user_id=1)

sess.add(cat1)
sess.commit()

cat2 = Category(name='Football',user_id=1)

sess.add(cat2)
sess.commit()
