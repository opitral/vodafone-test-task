from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from internal.models import Base
from internal.config import settings

engine = create_engine(
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost/{settings.POSTGRES_DB}"
)
Session = sessionmaker(bind=engine)
session = Session()


def create_db():
    Base.metadata.create_all(engine)


def drop_db():
    Base.metadata.drop_all(engine)
