import logging
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


DEFAULT_CDP_URL = "http://172.16.103.78:9225"
RETRY_TOTAL = 3
RETRY_BACKOFF_FACTOR = 0.5
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}


class Downloader:
    def __init__(self, timeout: int):
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.start()
        logger.info("Downloader 初始化完成，timeout=%d, cdp_url=%s", timeout, DEFAULT_CDP_URL)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def start(self):
        if self.page is not None:
            return
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(DEFAULT_CDP_URL)
            self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
            self.page = self.context.new_page()
            logger.info("已连接浏览器 CDP: %s", DEFAULT_CDP_URL)
        except Exception:
            self.close()
            raise

    def download(self, url: str) -> str:
        logger.info("开始下载: %s", url)
        if self.page is None:
            raise RuntimeError("Downloader has not been started")

        for retry_count in range(RETRY_TOTAL + 1):
            response = self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            try:
                self.page.wait_for_load_state("networkidle", timeout=min(self.timeout, 15) * 1000)
            except PlaywrightTimeoutError:
                logger.warning("等待 networkidle 超时，继续读取当前 DOM: %s", url)

            if response and response.status in RETRY_STATUS_CODES and retry_count < RETRY_TOTAL:
                sleep_seconds = RETRY_BACKOFF_FACTOR * (2 ** retry_count)
                logger.warning(
                    "下载返回临时 HTTP %s %s，%.1f 秒后重试 [%d/%d]: %s",
                    response.status,
                    response.status_text,
                    sleep_seconds,
                    retry_count + 1,
                    RETRY_TOTAL,
                    url,
                )
                time.sleep(sleep_seconds)
                continue

            if response and not response.ok and response.status != 304:
                raise RuntimeError(f"Failed to download {url}: HTTP {response.status} {response.status_text}")
            if response and response.status == 304:
                logger.warning("页面返回 HTTP 304 Not Modified，继续读取浏览器已加载 DOM: %s", url)

            content = self.page.content()
            logger.info("下载完成: %s, 内容长度=%d 字符", url, len(content))
            return content

        raise RuntimeError(f"Failed to download {url}")

    def close(self):
        logger.info("关闭 Downloader")
        if self.page:
            try:
                self.page.close()
            except Exception:
                logger.debug("关闭页面失败", exc_info=True)
            self.page = None
        self.browser = None
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                logger.debug("停止 Playwright 失败", exc_info=True)
            self.playwright = None
