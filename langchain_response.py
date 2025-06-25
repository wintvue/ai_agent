from pydantic import BaseModel


class InterviewResponse(BaseModel):
    topic: str
    summary: str
    sources: str
    tools_used: str
