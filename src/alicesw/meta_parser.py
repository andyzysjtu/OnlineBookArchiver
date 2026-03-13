from bs4 import BeautifulSoup

class MetaParser:
    def __init__(self, html: str):
        self.beautiful_soup = BeautifulSoup(html, 'html.parser')
    
    def extract_title(self) -> str:
        return self.beautiful_soup.find('div', class_='mu_h1').find("h1").text.strip()
    
    def extract_author(self) -> str:
        infos = self.beautiful_soup.find('div', class_='infos')
        if infos:
            for info in infos.find_all('span'):
                text = info.text.strip()
                if text.startswith('作者：'):
                    return text.split('作者：', 1)[1].strip()
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
        return chapters
    
    def extract(self, url: str) -> dict:
        return {
            'url': url,
            'title': self.extract_title(),
            'author': self.extract_author(),
            'chapters': self.extract_chapters()
        }