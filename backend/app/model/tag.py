from peewee import CharField

from .base_model import BaseModel


class Tag(BaseModel):
    """Etiqueta libre asociable a una transacción."""

    name = CharField(unique=True)
