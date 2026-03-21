import typing

import pydantic

import source.scalable


class Params(pydantic.BaseModel):
    name: str = pydantic.Field(min_length=1)


AnyParamsModel = typing.Union[
    source.scalable.Params,
    Params,  # Fallback base model
]
