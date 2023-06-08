from typing import TypeVar

from .db import models

SAModelObject = TypeVar("SAModelObject", bound=models.Base)
