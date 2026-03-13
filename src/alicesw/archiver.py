import argparse
import time
from urllib.parse import urlparse

import tomlkit
from alicesw import ARCHIVE
from alicesw.downloader import Downloader
from alicesw.meta_parser import MetaParser
from alicesw.chapter_parser import ChapterParser, URL_PREFIX


class Archiver:
    def __init__(self, url: str):
        self.url = url

    def run(self, timeout: int, delay: float) -> str:
        downloader = Downloader(timeout=timeout)

        html = downloader.download(self.url)
        meta_parser = MetaParser(html)
        meta = meta_parser.extract(self.url)

        dir = ARCHIVE / meta['title']
        dir.mkdir(parents=True, exist_ok=True)
        (dir / "meta.toml").write_text(tomlkit.dumps(meta), encoding="utf-8")

        for i, chapter_meta in enumerate(meta["chapters"]):
            chapter_url = URL_PREFIX + chapter_meta['url']
            chapter_id = urlparse(chapter_url).path.split('/')[-1].replace('.html', '')
            chapter_html = downloader.download(chapter_url)
            chapter_parser = ChapterParser(chapter_html)
            chapter = chapter_parser.extract()
            chapter_file = chapter.pop('content')
            chapter_meta.update(chapter)
            chapter_meta['id'] = chapter_id
            chapter_meta['txt'] = f"{chapter_id}.txt"
            (dir / chapter_meta['txt']).write_text(chapter_file, encoding="utf-8")
            time.sleep(delay)
        
        (dir / "meta_extend.toml").write_text(tomlkit.dumps(meta), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description='www.alicesw.com 电子书归档工具')
    parser.add_argument('--url', type=str, help='要归档的电子书 URL', required=True)
    parser.add_argument('--timeout', type=int, default=10, help='下载章节的超时时间（秒）')
    parser.add_argument('--delay', type=float, default=1, help='下载章节之间的延迟（秒）')
    args = parser.parse_args()
    
    archiver = Archiver(args.url)
    archiver.run(timeout=args.timeout, delay=args.delay)


if __name__ == '__main__':
    main()