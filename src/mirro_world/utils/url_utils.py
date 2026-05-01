from typing import Optional
from yarl import URL

class UrlUtils:
    @staticmethod
    def get_url_with_credentials(url: str, user: str, password: Optional[str]) -> URL:
        url_with_credentials: URL = URL(url)
        if password is None:
            return url_with_credentials
        return url_with_credentials.with_user(user).with_password(password)
