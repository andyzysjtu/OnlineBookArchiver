import argparse
import logging
import time
from urllib.parse import urlparse

import tomlkit
from alicesw import ARCHIVE
from alicesw.downloader import Downloader
from alicesw.meta_parser import MetaParser
from alicesw.chapter_parser import ChapterParser, URL_PREFIX

logger = logging.getLogger(__name__)


class Archiver:
    def __init__(self, url: str):
        self.url = url
        logger.info("Archiver 初始化，目标 URL=%s", url)

    def run(self, timeout: int, delay: float) -> str:
        logger.info("开始归档任务，timeout=%d, delay=%.1f", timeout, delay)
        downloader = Downloader(timeout=timeout)

        logger.info("下载书籍目录页: %s", self.url)
        html = downloader.download(self.url)
        meta_parser = MetaParser(html)
        meta = meta_parser.extract(self.url)

        dir = ARCHIVE / meta['title']
        dir.mkdir(parents=True, exist_ok=True)
        logger.info("创建归档目录: %s", dir)

        meta_path = dir / "meta.toml"
        meta_path.write_text(tomlkit.dumps(meta), encoding="utf-8")
        logger.info("保存元数据到: %s", meta_path)

        total_chapters = len(meta["chapters"])
        logger.info("共 %d 个章节待下载", total_chapters)

        downloaded_count = 0
        for i, chapter_meta in enumerate(meta["chapters"]):
            try:
                chapter_url = URL_PREFIX + chapter_meta['url']
                chapter_id = urlparse(chapter_url).path.split('/')[-1].replace('.html', '')
                logger.info("下载章节 [%d/%d]: %s (id=%s)", i + 1, total_chapters, chapter_url, chapter_id)

                chapter_html = downloader.download(chapter_url)
                chapter_parser = ChapterParser(chapter_html)
                chapter = chapter_parser.extract()
                chapter_file = chapter.pop('content')
                chapter_meta.update(chapter)
                chapter_meta['id'] = chapter_id
                chapter_meta['txt'] = f"{chapter_id}.txt"

                txt_path = dir / chapter_meta['txt']
                txt_path.write_text(chapter_file, encoding="utf-8")
                logger.info("保存章节内容到: %s (字数: %s)", txt_path, chapter_meta.get('word_count', 'unknown'))

                downloaded_count += 1
                logger.debug("延迟 %.1f 秒后继续", delay)
                time.sleep(delay)
            except Exception as e:
                logger.error("下载章节 [%d/%d] 时发生异常: %s，终止下载循环", i + 1, total_chapters, e)
                break
        
        meta_extend_path = dir / "meta_extend.toml"
        meta_extend_path.write_text(tomlkit.dumps(meta), encoding="utf-8")
        logger.info("保存扩展元数据到: %s", meta_extend_path)
        logger.info("归档任务完成，已成功下载 %d/%d 个章节", downloaded_count, total_chapters)

def main():
    parser = argparse.ArgumentParser(description='www.alicesw.com 电子书归档工具')
    parser.add_argument('--url', type=str, help='要归档的电子书 URL', required=True)
    parser.add_argument('--timeout', type=int, default=10, help='下载章节的超时时间（秒）')
    parser.add_argument('--delay', type=float, default=1, help='下载章节之间的延迟（秒）')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info("启动归档工具，参数: url=%s, timeout=%d, delay=%.1f", args.url, args.timeout, args.delay)
    
    archiver = Archiver(args.url)
    archiver.run(timeout=args.timeout, delay=args.delay)


if __name__ == '__main__':
    main()