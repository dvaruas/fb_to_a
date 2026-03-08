from typing import Self

import utils


class Config:
    url: str
    person_id: str
    portfolio_id: str
    output_path: str
    cookies: dict[str, str]
    headers: dict[str, str]

    def __init__(
        self,
        url: str,
        person_id: str,
        portfolio_id: str,
        cookie_string: str,
        output_path: str,
    ):
        self.url = url.strip()
        self.person_id = person_id.strip()
        self.portfolio_id = portfolio_id.strip()
        self.output_path = output_path.strip()
        cookie_string = cookie_string.strip()

        # validations
        if not url.startswith("https://"):
            raise ValueError("URL must start with 'https://'")
        if len(self.person_id) == 0:
            raise ValueError("Person ID cannot be empty")
        if len(self.portfolio_id) == 0:
            raise ValueError("Portfolio ID cannot be empty")
        if len(cookie_string) == 0:
            raise ValueError("Cookie string cannot be empty")

        self.cookies = {}
        for part in cookie_string.strip().split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)  # split only on first "="
                self.cookies[k] = v

        self.headers = {
            "accept": "*/*",
            "accept-language": "en,de-DE;q=0.9,de;q=0.8,en-US;q=0.7,no;q=0.6,bn;q=0.5",
            "content-type": "application/json",
        }

    @classmethod
    def from_json(cls, file_path: str) -> Self:
        return utils.load_config_from_json(cls, file_path=file_path)
