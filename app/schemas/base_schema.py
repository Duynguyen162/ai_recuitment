from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class ResponseSchema(BaseModel, Generic[T]):
    success:bool
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[dict] = None  # thông tin bổ sung như pagination, timestamp, v.v.