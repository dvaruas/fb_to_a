import typing

from source.scalable.params import Params


class Config:
    params: Params
    cookies: dict[str, str]
    headers: dict[str, str]

    def __init__(self, params: Params):
        self.params = params
        self.cookies = {}
        for part in params.cookie_string.strip().split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)  # split only on first "="
                self.cookies[k] = v

        self.headers = {
            "accept": "*/*",
            "accept-language": "en,de-DE;q=0.9,de;q=0.8,en-US;q=0.7,no;q=0.6,bn;q=0.5",
            "content-type": "application/json",
        }
