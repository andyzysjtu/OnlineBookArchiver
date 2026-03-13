import tomlkit

from alicesw.downloader import Downloader
from alicesw.meta_parser import MetaParser
from test_alicesw import RESOURCES

URL = 'https://www.alicesw.com/other/chapters/id/27686.html'

def test_meta_parser():
    downloader = Downloader(timeout = 10)
    html = downloader.download(URL)

    meta_parser = MetaParser(html)
    meta = meta_parser.extract(URL)

    assert meta == tomlkit.parse((RESOURCES / "meta.toml").read_text(encoding="utf-8"))
