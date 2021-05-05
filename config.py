from pydantic import BaseSettings


class AppSettings(BaseSettings):
    mapbox_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
