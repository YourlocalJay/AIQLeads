from typing import Dict, Any
from requests.exceptions import RequestException
import requests
import backoff


class APIIntegration:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    @backoff.on_exception(backoff.expo, RequestException, max_tries=3)
    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(
                method=method, url=url, timeout=self.timeout, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise APIIntegrationError(f"Request failed: {str(e)}")


class APIIntegrationError(Exception):
    pass
