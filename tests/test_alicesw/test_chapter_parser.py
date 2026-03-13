import io
import tomlkit
from urllib.parse import urlparse
from alicesw.downloader import Downloader
from alicesw.chapter_parser import ChapterParser, URL_PREFIX
from test_alicesw import RESOURCES

def test_chapter_parser():
    meta = tomlkit.parse((RESOURCES / "meta.toml").read_text(encoding="utf-8"))

    for index in range(0, 2):
        url = meta["chapters"][index]['url']

        id = urlparse(url).path.split('/')[-1].replace('.html', '')

        downloader = Downloader(timeout = 10)
        html = downloader.download(URL_PREFIX + url)

        chapter_parser = ChapterParser(html)
        chapter = chapter_parser.extract()

        temp_file = io.StringIO()
        temp_file.write(chapter['content'])
        temp_file.seek(0)

        assert temp_file.read() == (RESOURCES / f"{id}.txt").read_text(encoding="utf-8")