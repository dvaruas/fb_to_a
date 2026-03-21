import typing

import pydantic

import destination.parqet


class Params(pydantic.BaseModel):
    name: str = pydantic.Field(min_length=1)


AnyParamsModel = typing.Union[
    destination.parqet.Params,
    Params,  # Fallback base model
]
