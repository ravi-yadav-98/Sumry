from pydantic import BaseModel

class URLRequest(BaseModel):
    url: str

class SummarizationResponse(BaseModel):
    content: str
    status: str = "success"

class ErrorResponse(BaseModel):
    error: str
    details: str = ""
    status: str = "error"