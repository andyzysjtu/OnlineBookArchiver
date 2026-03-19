import tomlkit

from alicesw.downloader import Downloader
from alicesw.meta_parser import MetaParser
from test_alicesw import RESOURCES

def test_meta_parser():
    expected_meta = tomlkit.parse((RESOURCES / "meta.toml").read_text(encoding="utf-8"))

    downloader = Downloader(timeout = 10)
    html = downloader.download(expected_meta["url"])

    meta_parser = MetaParser(html)
    meta = meta_parser.extract(expected_meta["url"])

    assert meta == expected_meta
