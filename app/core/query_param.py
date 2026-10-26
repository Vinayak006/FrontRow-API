from typing import Annotated

from fastapi import Query
from pydantic import StringConstraints

SearchText = Annotated[
    str,
    StringConstraints(strip_whitespace=True),
]

SearchQuery = Annotated[SearchText | None, Query()]
