from pydantic import BaseModel, ConfigDict, Field


class ReaderAddRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class ReaderAddResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    library_card_number: str
    first_name: str
    last_name: str