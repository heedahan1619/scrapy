import scrapy
from self_study_scrapy.items import SelfStudyScrapyItem

class NewsSpider(scrapy.Spider):
    """크롤링할 사이트의 동작을 정의"""
    
    name = 'news' # 스파이더 이름
    media = '교통신문(GyotongN)'
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    media_url = "http://www.gyotongn.com/"
    page_request_range = 10
    
    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드"""
        return[
            scrapy.Request(
                url = self.media_url,
                headers=self.headers,
                callback=self.parse_category
            )
        ]
            
            
    def parse_category(self, response):
        """카테고리 이름 수집"""
        print(f"\n url: {self.media_url}")
        
        category_name = response.xpath("//ul[@class='vertical menu']/li/a/text()").getall()
        print(f"\n category_name: {category_name}")
