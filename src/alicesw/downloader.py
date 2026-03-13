import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

RETRY = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
ADAPTER = HTTPAdapter(max_retries=RETRY)

class Downloader:
    def __init__(self, timeout: int):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.session.mount("http://", ADAPTER)
        self.session.mount("https://", ADAPTER)

    def download(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.content.decode(response.apparent_encoding, errors="replace")
