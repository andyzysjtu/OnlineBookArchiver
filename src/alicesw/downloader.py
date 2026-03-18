import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

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
        logger.info("Downloader 初始化完成，timeout=%d, User-Agent=%s", timeout, USER_AGENT)

    def download(self, url: str) -> str:
        logger.info("开始下载: %s", url)
        response = self.session.get(url, timeout=self.timeout)
        logger.debug("收到响应: status_code=%d, content_length=%s", response.status_code, response.headers.get('Content-Length', 'unknown'))
        response.raise_for_status()
        content = response.content.decode(response.apparent_encoding, errors="replace")
        logger.info("下载完成: %s, 编码=%s, 内容长度=%d 字符", url, response.apparent_encoding, len(content))
        return content
