import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

URL_PREFIX = 'https://www.alicesw.com'

class ChapterParser:
    def __init__(self, html: str):
        logger.debug("ChapterParser 初始化，HTML 长度=%d 字符", len(html))
        self.beautiful_soup = BeautifulSoup(html, 'html.parser')

    def extract_name(self) -> str:
        name = self.beautiful_soup.find('h3', class_='j_chapterName').text.strip()
        logger.debug("提取到章节名: %s", name)
        return name
    
    def extract_word_count(self) -> str:
        word_count = self.beautiful_soup.find('span', class_='j_chapterWordCut').text.strip()
        logger.debug("提取到字数: %s", word_count)
        return word_count
    
    def extract_update_time(self) -> str:
        update_time = self.beautiful_soup.find('span', class_='j_updateTime').text.strip()
        logger.debug("提取到更新时间: %s", update_time)
        return update_time
    
    def extract_content(self) -> str:
        content = self.beautiful_soup.find('div', class_='read-content j_readContent user_ad_content').get_text(separator='\n', strip=False)
        logger.debug("提取到正文内容，长度=%d 字符", len(content))
        return content

    def extract(self) -> dict:
        logger.debug("开始提取章节详情")
        result = {
            'name': self.extract_name(),
            'word_count': self.extract_word_count(),
            'update_time': self.extract_update_time(),
            'content': self.extract_content().lstrip('\n')
        }
        logger.debug("章节详情提取完成: 名称=%s, 字数=%s", result['name'], result['word_count'])
        return result