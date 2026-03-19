import tomlkit

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