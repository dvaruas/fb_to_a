import typing

from destination.parqet.params import Params


class Config:
    params: Params

    def __init__(self, params: Params):
        self.params = params
