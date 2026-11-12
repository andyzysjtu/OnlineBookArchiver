from unittest.mock import call

from alicesw.batch_archiver import BatchArchiver


def test_iter_urls_finds_nested_meta_files_and_skips_invalid_ones(tmp_path):
    first_meta = tmp_path / "a" / "meta.toml"
    first_meta.parent.mkdir()
    first_meta.write_text('url = "https://example.com/a"\n', encoding="utf-8")

    second_meta = tmp_path / "nested" / "b" / "meta.toml"
    second_meta.parent.mkdir(parents=True)
    second_meta.write_text('url = "https://example.com/b"\n', encoding="utf-8")

    invalid_meta = tmp_path / "missing-url" / "meta.toml"
    invalid_meta.parent.mkdir()
    invalid_meta.write_text('title = "missing url"\n', encoding="utf-8")

    assert list(BatchArchiver(tmp_path).iter_urls()) == [
        (first_meta, "https://example.com/a"),
        (second_meta, "https://example.com/b"),
    ]


def test_run_calls_archiver_for_every_url_and_continues_after_failure(
    tmp_path, monkeypatch
):
    for directory, url in (
        ("a", "https://example.com/a"),
        ("b", "https://example.com/b"),
        ("c", "https://example.com/c"),
    ):
        meta_path = tmp_path / directory / "meta.toml"
        meta_path.parent.mkdir()
        meta_path.write_text(f'url = "{url}"\n', encoding="utf-8")

    archiver_calls = []
    run_calls = []

    class FakeArchiver:
        def __init__(self, url):
            self.url = url
            archiver_calls.append(url)

        def run(self, timeout, delay, meta_only=False):
            run_calls.append(
                call(
                    self.url,
                    timeout=timeout,
                    delay=delay,
                    meta_only=meta_only,
                )
            )
            if self.url.endswith("/b"):
                raise RuntimeError("download failed")

    monkeypatch.setattr("alicesw.batch_archiver.Archiver", FakeArchiver)

    BatchArchiver(tmp_path).run(timeout=20, delay=0.5)

    assert archiver_calls == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]
    assert run_calls == [
        call("https://example.com/a", timeout=20, delay=0.5, meta_only=False),
        call("https://example.com/b", timeout=20, delay=0.5, meta_only=False),
        call("https://example.com/c", timeout=20, delay=0.5, meta_only=False),
    ]


def test_meta_mode_sums_remaining_chapters(tmp_path, monkeypatch, caplog):
    for directory, url in (
        ("a", "https://example.com/a"),
        ("b", "https://example.com/b"),
    ):
        meta_path = tmp_path / directory / "meta.toml"
        meta_path.parent.mkdir()
        meta_path.write_text(f'url = "{url}"\n', encoding="utf-8")

    run_calls = []

    class FakeArchiver:
        def __init__(self, url):
            self.url = url

        def run(self, timeout, delay, meta_only=False):
            run_calls.append(
                call(
                    self.url,
                    timeout=timeout,
                    delay=delay,
                    meta_only=meta_only,
                )
            )
            return 2 if self.url.endswith("/a") else 3

    monkeypatch.setattr("alicesw.batch_archiver.Archiver", FakeArchiver)
    caplog.set_level("INFO", logger="alicesw.batch_archiver")

    BatchArchiver(tmp_path).run(timeout=10, delay=0, meta_only=True)

    assert run_calls == [
        call("https://example.com/a", timeout=10, delay=0, meta_only=True),
        call("https://example.com/b", timeout=10, delay=0, meta_only=True),
    ]
    assert "成功 2 本，失败 0 本，共计还需下载 5 个章节" in caplog.text
    assert "缺失章节的书籍：" in caplog.text
    assert "- a：2 个章节" in caplog.text
    assert "- b：3 个章节" in caplog.text
