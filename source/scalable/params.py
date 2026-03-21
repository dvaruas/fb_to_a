import pathlib
import typing

import pydantic


class Params(pydantic.BaseModel):
    name: typing.Literal["scalable"]

    url: pydantic.HttpUrl
    person_id: str = pydantic.Field(min_length=1)
    portfolio_id: str = pydantic.Field(min_length=1)
    cookie_string: str = pydantic.Field(min_length=1)
    output_path: pathlib.Path
