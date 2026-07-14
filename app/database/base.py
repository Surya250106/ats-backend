from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in SQLAlchemy 2.x.
    """
    pass


# Note: Do not import models here to prevent circular imports.
# Models should be imported explicitly (e.g. `import app.models`)
# where Base.metadata needs to be fully populated (such as in alembic/env.py or tests/conftest.py).

