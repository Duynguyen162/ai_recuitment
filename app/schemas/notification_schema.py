from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    is_read: bool

    class Config:
        from_attributes = True
