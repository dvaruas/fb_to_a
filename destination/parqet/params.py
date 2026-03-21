import pathlib
import typing

import pydantic


class Params(pydantic.BaseModel):
    name: typing.Literal["parqet"]

    output_path: pathlib.Path
