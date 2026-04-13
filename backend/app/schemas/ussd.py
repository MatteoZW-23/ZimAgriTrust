from pydantic import BaseModel


class USSDRequest(BaseModel):
    session_id: str
    phone_number: str
    text: str = ""


class USSDResponse(BaseModel):
    message: str
    end_session: bool = False
