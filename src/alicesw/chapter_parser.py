from bs4 import BeautifulSoup

URL_PREFIX = 'https://www.alicesw.com'

class ChapterParser:
    def __init__(self, html: str):
        self.beautiful_soup = BeautifulSoup(html, 'html.parser')

    def extract_name(self) -> str:
        return self.beautiful_soup.find('h3', class_='j_chapterName').text.strip()
    
    def extract_word_count(self) -> str:
        return self.beautiful_soup.find('span', class_='j_chapterWordCut').text.strip()
    
    def extract_update_time(self) -> str:
        return self.beautiful_soup.find('span', class_='j_updateTime').text.strip()
    
    def extract_content(self) -> str:
        return self.beautiful_soup.find('div', class_='read-content j_readContent user_ad_content').get_text(separator='\n', strip=False)

    def extract(self) -> dict:
        return {
            'name': self.extract_name(),
            'word_count': self.extract_word_count(),
            'update_time': self.extract_update_time(),
            'content': self.extract_content().lstrip('\n')
        }