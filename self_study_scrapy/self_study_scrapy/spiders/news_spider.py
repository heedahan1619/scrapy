import scrapy
from items import SelfStudyScrapyItem

class NewsSpider(scrapy.Spider):
    """크롤링할 사이트의 동작을 정의"""
    
    name = 'news' # 스파이더 이름
    media = '아주경제(AjuNews)'
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    url = "https://www.ajunews.com"
    category_news_url = "https://www.ajunews.com/{}?page={}"
    page_request_range = 10
    
    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드"""
        return[
            scrapy.Request(
                url = self.url,
                headers=self.headers,
                callback=self.parse_media_category
            )
        ]
            
            
    def parse_media_category(self, response):
        """언론사 카테고리 추출"""
        
        # 언론사 카테고리 코드 리스트 생성
        category_code_list = []
        category_codes= response.xpath("//ul[@class='all clearfix']//a/@href").getall()
        # print(f"category_codes: {category_codes}")
        for category_code in category_codes:
            # print(f"category_code: {category_code}")
            split = category_code.split("/")[3:]
            if len(split) == 3:
                category = split[0] + "/" + split[1] + "/" + split[2]
            elif len(split) == 2:
                category = split[0] + "/" + split[1] 
            else:
                category = split[0]
            print(f"category: {category}")
            
            category_code_list.append(category)
        # print(f"category_code_list: {category_code_list}")
        
        # 언론사 카테고리 이름 리스트 생성
        category_name_list = response.xpath("//ul[@class='all clearfix']//a/text()").getall()
        # print(f"category_name_list: {category_name_list}")
        
        # 언론사 카테고리 딕셔너리 생성
        category_dict = dict(zip(category_code_list, category_name_list))
        # print(f"category_dict: {category_dict}")
    
        for category_code in category_code_list:
            for page_num in range(1, self.page_request_range+1):
                yield scrapy.Request(
                    url=self.category_news_url.format(category, page_num),
                    headers=self.headers,
                    # callback=self.parse_category_news_list,
                    meta={
                            "media_category": category
                        }
                )