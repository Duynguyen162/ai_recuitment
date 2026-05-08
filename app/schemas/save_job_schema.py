from pydantic import BaseModel

class SaveJobResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int

    class Config:
        from_attributes = True