import argparse
import logging
from collections.abc import Iterator
from pathlib import Path

import tomlkit

from alicesw import ARCHIVE
from alicesw.archiver import Archiver

logger = logging.getLogger(__name__)


class BatchArchiver:
    """Archive every AliceSW book already registered in the archive directory."""

    def __init__(self, archive_dir: Path = ARCHIVE):
        self.archive_dir = Path(archive_dir)

    def iter_urls(self) -> Iterator[tuple[Path, str]]:
        """Yield each valid ``meta.toml`` path and its top-level URL."""
        meta_paths = sorted(self.archive_dir.rglob("meta.toml"), key=str)
        logger.info("在 %s 下找到 %d 个 meta.toml", self.archive_dir, len(meta_paths))

        for meta_path in meta_paths:
            try:
                meta = tomlkit.parse(meta_path.read_text(encoding="utf-8"))
                url = meta.get("url")
                if not isinstance(url, str) or not url.strip():
                    raise ValueError("缺少有效的顶层 url")
            except (OSError, tomlkit.exceptions.ParseError, ValueError) as error:
                logger.error("无法读取元数据 %s: %s，已跳过", meta_path, error)
                continue

            yield meta_path, url.strip()

    def run(self, timeout: int, delay: float, meta_only: bool = False) -> None:
        archived_count = 0
        failed_count = 0
        remaining_chapters = 0
        books_with_missing_chapters = []

        for meta_path, url in self.iter_urls():
            logger.info("开始处理 %s: %s", meta_path.parent, url)
            try:
                remaining = Archiver(url).run(
                    timeout=timeout,
                    delay=delay,
                    meta_only=meta_only,
                )
                archived_count += 1
                if meta_only and remaining is not None:
                    remaining_chapters += remaining
                    if remaining > 0:
                        books_with_missing_chapters.append(
                            (meta_path.parent.name, remaining)
                        )
            except Exception:
                failed_count += 1
                logger.exception("处理 %s 时发生异常，继续处理下一本", meta_path.parent)

        if meta_only:
            logger.info(
                "批量 meta 更新完成，成功 %d 本，失败 %d 本，共计还需下载 %d 个章节",
                archived_count,
                failed_count,
                remaining_chapters,
            )
            if books_with_missing_chapters:
                logger.info("缺失章节的书籍：")
                for title, missing_count in books_with_missing_chapters:
                    logger.info("- %s：%d 个章节", title, missing_count)
            else:
                logger.info("缺失章节的书籍：无")
        else:
            logger.info("批量归档完成，成功 %d 本，失败 %d 本", archived_count, failed_count)


def main() -> None:
    parser = argparse.ArgumentParser(description="批量更新 archive/alicesw 中的电子书")
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=ARCHIVE,
        help="包含各电子书 meta.toml 的归档目录",
    )
    parser.add_argument("--timeout", type=int, default=10, help="下载章节的超时时间（秒）")
    parser.add_argument("--delay", type=float, default=1, help="下载章节之间的延迟（秒）")
    parser.add_argument(
        "--meta",
        action="store_true",
        help="仅更新各书元数据并汇总待下载章节，不下载章节内容",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    BatchArchiver(args.archive_dir).run(
        timeout=args.timeout,
        delay=args.delay,
        meta_only=args.meta,
    )


if __name__ == "__main__":
    main()
