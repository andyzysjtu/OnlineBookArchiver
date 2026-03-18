import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class MetaParser:
    def __init__(self, html: str):
        logger.info("MetaParser 初始化，HTML 长度=%d 字符", len(html))
        self.beautiful_soup = BeautifulSoup(html, 'html.parser')
        logger.debug("BeautifulSoup 解析完成")
    
    def extract_title(self) -> str:
        title = self.beautiful_soup.find('div', class_='mu_h1').find("h1").text.strip()
        logger.info("提取到书名: %s", title)
        return title
    
    def extract_author(self) -> str:
        infos = self.beautiful_soup.find('div', class_='infos')
        if infos:
            for info in infos.find_all('span'):
                text = info.text.strip()
                if text.startswith('作者：'):
                    author = text.split('作者：', 1)[1].strip()
                    logger.info("提取到作者: %s", author)
                    return author
        logger.warning("未找到作者信息，使用默认值 'Unknown'")
        return 'Unknown'

    def extract_chapters(self) -> list:
        chapters = []
        mulu_list = self.beautiful_soup.find('ul', class_='mulu_list')
        if mulu_list:
            for li in mulu_list.find_all('li'):
                a_tag = li.find('a')
                if a_tag:
                    chapter_index = a_tag.text.strip()
                    chapter_url = a_tag['href']
                    chapters.append({'index': chapter_index, 'url': chapter_url})
            logger.info("提取到 %d 个章节目录", len(chapters))
        else:
            logger.warning("未找到章节目录列表 (ul.mulu_list)")
        return chapters
    
    def extract(self, url: str) -> dict:
        logger.info("开始提取元数据，URL=%s", url)
        result = {
            'url': url,
            'title': self.extract_title(),
            'author': self.extract_author(),
            'chapters': self.extract_chapters()
        }
        logger.info("元数据提取完成: 书名=%s, 作者=%s, 章节数=%d", result['title'], result['author'], len(result['chapters']))
        return result