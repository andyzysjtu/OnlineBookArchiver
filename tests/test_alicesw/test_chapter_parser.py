import io
from urllib.parse import urlparse

import tomlkit

from alicesw.chapter_parser import URL_PREFIX, ChapterParser
from alicesw.downloader import Downloader
from test_alicesw import RESOURCES


def test_chapter_parser():
    meta = tomlkit.parse((RESOURCES / "meta.toml").read_text(encoding="utf-8"))

    with Downloader(timeout=10) as downloader:
        for index in range(2):
            url = meta["chapters"][index]['url']

            id = urlparse(url).path.split('/')[-1].replace('.html', '')

            html = downloader.download(URL_PREFIX + url)

            chapter_parser = ChapterParser(html)
            chapter = chapter_parser.extract()

            temp_file = io.StringIO()
            temp_file.write(chapter['content'])
            temp_file.seek(0)

            assert temp_file.read() == (RESOURCES / f"{id}.txt").read_text(encoding="utf-8")
