import datetime

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
        total_category_list = []
        media_category_dict = {}
        media_category_sub_dict = {}
        
        for category_info in (response.xpath("//ul[@class='all clearfix']/li/dl")):
            # print(f"\n 카테고리 정보: {category_info}")
            
            # 대분류 추출
            for category in category_info.xpath("dt/a/@href").getall():
                if len(category.split("/")[3:]) > 1:
                    media_category_code = category.split("/")[3:][0] + "/" + category.split("/")[3:][1]
                else:
                    media_category_code = category.split("/")[3:][0]
                # print(f"\n 카테고리 대분류 code: {media_category_code}")
        
            media_category_name = category_info.xpath("dt/a/text()").get()
            # print(f"\n 카테고리 대분류 name: {media_category_name}")
            
            media_category_dict[media_category_code] = media_category_name
        
            # 소분류 추출
            media_category_sub_info = category_info.xpath("dd/a")
            
            for media_category_sub in media_category_sub_info:
                if len(media_category_sub.xpath("@href").get().split("/")[3:]) == 3:
                    media_category_sub_code = media_category_sub.xpath("@href").get().split("/")[3:][0] + "/" + media_category_sub.xpath("@href").get().split("/")[3:][1] + "/" + media_category_sub.xpath("@href").get().split("/")[3:][2]
                elif len(media_category_sub.xpath("@href").get().split("/")[3:]) == 2:
                    media_category_sub_code = media_category_sub.xpath("@href").get().split("/")[3:][0] + "/" + media_category_sub.xpath("@href").get().split("/")[3:][1]
                else:
                    media_category_sub_code = media_category_sub.xpath("@href").get().split("/")[3:][0]
                  
                # print(f"\n 카테고리 소분류 code: {media_category_sub_code}")
                  
                media_category_sub_name = media_category_sub.xpath("text()").get()    
                # print(f"\n 카테고리 소분류 name: {media_category_sub_name}")
                
                media_category_sub_dict[media_category_sub_code] = media_category_sub_name

        # print(f"\n 카테고리 대분류 dict: {media_category_dict}")
        # print(f"\n 카테고리 소분류 dict: {media_category_sub_dict}")
        
        for category_key in media_category_dict.keys():
            total_category_list.append(category_key)
        
        for category_sub_key in media_category_sub_dict.keys():
            total_category_list.append(category_sub_key)
            
        # print(f"\n 전체 카테고리 list: {total_category_list}")
      
        total_category_list_dict = {**media_category_dict, **media_category_sub_dict}
        # print(f"\n 전체 카테고리 dict: {total_category_list_dict}")
        
        for total_category in total_category_list:
            for page_num in range(1, self.page_request_range+1):
                yield scrapy.Request(
                    url=self.category_news_list_url.format(total_category, page_num),
                    headers=self.headers,
                    callback=self.parse_category_news_list,
                    meta={
                            "media_category": media_category_code,
                            "media_category_sub": media_category_sub_code
                        }
                )
    
    def parse_category_news_list(self, response):
        """뉴스 탭 메뉴별 목록 페이지를 분석합니다.
        """
        media_category = response.meta["media_category"]
        media_category_sub = response.meta["media_category_sub"]
        print(f"\n 카테고리 대분류: {media_category}")
        print(f"\n 카테고리 소분류: {media_category_sub}")
        
        if response.url == "https://www.ajunews.com/"+ media_category:
            page_num = 1
        else:
            page_num = (response.url).split('/')[-1]
            
        # 목록 확인
        is_next_news_list = False
        for news_list in response.xpath("//ul[@class='news_list']/li/div[@class='text_area']"):
            # 날짜 확인
            date_elements = news_list.xpath("ul[@class='date']/li/text()").getall()
            date = date_elements[0] + " " + date_elements[1]
            # print(f"날짜: {date}")
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            # print(f"datetime 날짜: {date}")
            if self.start_date <= date <= self.end_date:
                print(f"\n 뉴스 리스트 url: {response.url}")
                print(f"뉴스 날짜: {date}")
                is_next_news_list = True
                category_news_page_url = "https:" + news_list.xpath("a[@class='tit']/@href").get()
                print(f"뉴스 링크: {category_news_page_url}")
                yield scrapy.Request(
                    url=category_news_page_url.format(self.total_category, page_num),
                    headers=self.headers,
                    callback=self.parse_news_page,
                    meta={
                        "date": date,
                        "media_category": media_category,
                        "media_category_sub": media_category_sub
                    }
                )
            elif self.end_date < date:
                is_next_news_list = True
        # 다른 뉴스 목록을 더 살펴보아야 하는 경우
        if is_next_news_list:
            next_page_num = int(page_num)+self.page_request_range
            yield scrapy.Request(
                url=self.category_news_list_url.format(self.total_category, str(next_page_num)),
                headers=self.headers,
                callback=self.parse_category_news_page,
                meta={
                        "media_category": media_category,
                        "media_category_sub": media_category_sub
                } 
            )

    def parse_category_news_page(self, response):
        print(f"\t{response.url}")
        item = SelfStudyScrapyItem()
        item["save_method"] = self.save_method
        item["inp_date"] = response.meta["date"]
        item["category"] = "스타트업"
        item["media_category"] = response.meta["media_category"]
        item["media_category_sub"] = response.meta["media_category_sub"]
        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language
        item["title"] = response.xpath("//div[@class='view']/article/div[@class='inner']/h1/text()").get().strip()
        item["content"] = " ".join(response.xpath("//div[@id='articleBody']/text()").getall())


        print(f"\n 기사 카테고리 대분류: {item["media_category"]}")
        print(f"\n 기사 카테고리 소분류: {item["media_category_sub"]}")
        print(f"\n 기사 날짜: {item["inp_date"]}")
        print(f"\n 기사 제목: {item["title"]}")
        print(f"\n 기사 내용: {item["content"]}")

        yield item

