import tomlkit

from alicesw.archiver import (
    Archiver,
    completed_chapters_from,
    count_remaining_chapters,
)
from test_alicesw import RESOURCES


def test_meta_uncompleted():
    meta = tomlkit.parse((RESOURCES / "meta.toml").read_text(encoding="utf-8"))
    meta_extend = tomlkit.parse((RESOURCES / "meta_extend.toml").read_text(encoding="utf-8"))

    completed_urls = {
        ch["url"] for ch in meta_extend.get("chapters", []) if "name" in ch and "word_count" in ch and "update_time" in ch and "id" in ch and "txt" in ch
    }

    uncompleted_chapters = []
    for i, chapter_meta in enumerate(meta["chapters"]):
        if chapter_meta["url"] in completed_urls:
            continue
        uncompleted_chapters.append(chapter_meta)

    assert len(uncompleted_chapters) == 6
    assert uncompleted_chapters[0]["index"] == "第61章 情欲卫生间（上）"
    assert uncompleted_chapters[1]["index"] == "第62章 情欲卫生间（下）"
    assert uncompleted_chapters[2]["index"] == "第63章 丢失"
    assert uncompleted_chapters[3]["index"] == "第64章 失去（上）"
    assert uncompleted_chapters[4]["index"] == "第65章 失去（下）"
    assert uncompleted_chapters[5]["index"] == "第66章 大结局"


def test_count_remaining_chapters():
    meta = tomlkit.parse((RESOURCES / "meta.toml").read_text(encoding="utf-8"))
    meta_extend = tomlkit.parse(
        (RESOURCES / "meta_extend.toml").read_text(encoding="utf-8")
    )

    completed_chapters = completed_chapters_from(meta_extend)

    assert count_remaining_chapters(meta, completed_chapters) == 6


def test_meta_mode_creates_initial_meta_extend_without_downloading_chapters(
    tmp_path, monkeypatch
):
    book_meta = {
        "url": "https://example.com/book",
        "title": "测试书籍",
        "author": "测试作者",
        "chapters": [
            {"index": "第一章", "url": "/chapter/1.html"},
            {"index": "第二章", "url": "/chapter/2.html"},
        ],
    }
    downloaded_urls = []
    downloader_closed = []

    class FakeDownloader:
        def __init__(self, timeout):
            assert timeout == 10

        def download(self, url):
            downloaded_urls.append(url)
            return "catalogue html"

        def close(self):
            downloader_closed.append(True)

    class FakeMetaParser:
        def __init__(self, html):
            assert html == "catalogue html"

        def extract(self, url):
            assert url == book_meta["url"]
            return book_meta

    monkeypatch.setattr("alicesw.archiver.ARCHIVE", tmp_path)
    monkeypatch.setattr("alicesw.archiver.Downloader", FakeDownloader)
    monkeypatch.setattr("alicesw.archiver.MetaParser", FakeMetaParser)

    remaining = Archiver(book_meta["url"]).run(
        timeout=10, delay=0, meta_only=True
    )

    archive_dir = tmp_path / book_meta["title"]
    saved_meta = tomlkit.parse(
        (archive_dir / "meta.toml").read_text(encoding="utf-8")
    )
    saved_meta_extend = tomlkit.parse(
        (archive_dir / "meta_extend.toml").read_text(encoding="utf-8")
    )
    assert saved_meta_extend == saved_meta
    assert remaining == 2
    assert downloaded_urls == [book_meta["url"]]
    assert downloader_closed == [True]

    saved_meta_extend["chapters"][0].update(
        {
            "name": "第一章",
            "word_count": "100",
            "update_time": "2026-08-19",
            "id": "1",
            "txt": "1.txt",
        }
    )
    meta_extend_path = archive_dir / "meta_extend.toml"
    existing_meta_extend = tomlkit.dumps(saved_meta_extend)
    meta_extend_path.write_text(existing_meta_extend, encoding="utf-8")

    remaining = Archiver(book_meta["url"]).run(
        timeout=10, delay=0, meta_only=True
    )

    assert remaining == 1
    assert meta_extend_path.read_text(encoding="utf-8") == existing_meta_extend
    assert downloaded_urls == [book_meta["url"], book_meta["url"]]
    assert downloader_closed == [True, True]
