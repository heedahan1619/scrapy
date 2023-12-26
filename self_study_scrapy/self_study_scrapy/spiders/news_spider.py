from datetime import datetime, timedelta

import re
import os
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from items import SelfStudyScrapyItem

class Stella1Spider(scrapy.Spider):
    
    """스파이더 설정"""
    # 스파이더 이름
    name = "stella1"    
    
    # 언론사
    origin_media = "이투데이(Etoday)"
    
    language = "ko" 
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    """url"""
    # 메인 홈페이지 url
    main_url = "https://www.etoday.co.kr"
    
    # 카테고리 뉴스 목록 url
    category_news_list_url = "https://www.etoday.co.kr{}&page={}"
    
    # 비동기 카테고리 목록 url
    async_category_list_url = "http://www.etoday.co.kr{}"
    
    # 페이지 요청 범위
    page_request_range = 10
    
    #  언론사 카테고리 dict
    media_dict = {} # 전체 카테고리 dict 
    media_category_dict = {} # 대분류 카테고리 dict


    def __init__(
            self, 

            # # 날짜 지정
            # start_date = "2023-12-24",
            # end_date = "2023-12-25",
            
            # 날짜 입력
            start_date_input = None,
            end_date_input = None,
            
            # # 카테고리 입력
            # user_input_category = None,
            
            save_method="json"
        ):
    
        # # 날짜 지정
        # self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        # self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
        # 날짜 입력
        if start_date_input is None:
            start_date_input = input("시작 날짜 입력(YYYYMMDD): ")
        if end_date_input is None:
            end_date_input = input("종료 날짜 입력(YYYYMMDD): ")
            
        # 날짜 변환 및 유효성 확인
        def transform_date(date_input):
            try:
                return datetime.strptime(date_input, "%Y%m%d")
            except ValueError:
                print("올바른 날짜 형식이 아닙니다.")
                return None

        # 날짜 datetime 형태 변환
        def transform_date_output(date):
            return date.strftime("%Y-%m-%d")
        
        self.start_date_input = start_date_input
        self.start_date_input = end_date_input
        self.start_date = transform_date(start_date_input)
        self.end_date = transform_date(end_date_input) + timedelta(days=1) - timedelta(seconds=1)

        # start_date와 end_date의 유효성을 확인
        assert self.start_date is not None and self.end_date is not None, "유효하지 않은 날짜 형식이 입력되었습니다."
        assert self.start_date.timestamp() <= self.end_date.timestamp(), "end_date가 start_date보다 앞에 있습니다."
        
        # # 카테고리 입력
        # if user_input_category is None:
        #     user_input_category = input("카테고리를 입력하세요 : ")
        
        self.save_method = save_method
        assert self.save_method in ("json"), "선택할 수 있는 save_method가 아닙니다."


    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드"""
        
        # 언론사명
        media = str(self.origin_media.split("(")[0])
        print(f"\n언론사: {media}")  
        
        return [
            scrapy.Request(
                
                # 메인 홈페이지로 이동
                url=self.main_url,
                
                headers=self.headers,
                
                # 언론사 카테고리 추출 함수로 연결
                callback=self.parse_media_category
            )
        ]
        

    def parse_media_category(self, response):   
        """언론사 카테고리 추출 함수"""  

        for category_info in response.xpath("//div[@class='allmenuCont']/ul/li/dl"):
            """카테고리 대분류"""
            for category in category_info.xpath("dt/a"):
                
                # 대분류 카테고리 코드
                media_category_code = category.xpath("@href").get()
                # print(f"\n대분류 코드: {media_category_code}")
                
                # 대분류 카테고리 이름    
                media_category = category.xpath("text()").get()
                # print(f"\n대분류: {media_category}")

                # 대분류 카테고리 딕셔너리
                self.media_category_dict[media_category_code] = media_category
            
            """카테고리 소분류"""    
            
            # 소분류 카테고리 딕셔너리 초기화
            media_category_sub_dict = {}
                
            for category_sub in category_info.xpath("dd/a"):
                # print(f"소분류 요소: {category_sub}")

                # 소분류 카테고리 코드
                media_category_sub_code = category_sub.xpath("@href").get()
                # print(f"소분류 코드: {media_category_sub_code}")
                
                # 소분류 카테고리 이름   
                media_category_sub = category_sub.xpath("text()").get()
                # print(f"소분류: {media_category_sub}")
                
                # 소분류 카테고리 딕셔너리
                media_category_sub_dict[media_category_sub_code] = media_category_sub
                # print(f"\n소분류 카테고리 dict: {media_category_sub_dict}")
                
                
            """카테고리 딕셔너리"""
        
            # 대분류 카테고리를 key로 하고, 소분류 카테고리 정보를 value로 하는 media_dict
            self.media_dict[media_category] = media_category_sub_dict
            
        # print(f"\n대분류 dict: {self.media_category_dict}")  
        # print(f"\n전체 카테고리 dict: {self.media_dict}")
                

        """스크래피 요청"""    
        # 카테고리 추출
        for media_category, media_category_sub_dict in self.media_dict.items():
            # print("대분류", media_category)
            # print(media_category_sub_dict)
            
            for media_category_sub_code, media_category_sub in media_category_sub_dict.items():
                # print("소분류 코드", media_category_sub_code)
                
                # 페이지 지정
                for page_num in range(1, self.page_request_range+1):
                    category = media_category_sub_code
                    # print("소분류 코드", category)
                    
                    # url 구분
                    if "MID" in category:
                        url = self.category_news_list_url.format(category, page_num)
                    else:
                        url = self.async_category_list_url.format(category)
                    # print(f"\n목록 url: {url}")

                    # 스크래피 요청
                    yield scrapy.Request(
                    
                        url = url,      
                        headers=self.headers,
                        
                        # 카테고리별 뉴스 목록 페이지 확인 함수로 연결
                        callback=self.parse_category_news_list,
                        
                        meta={
                            "media_code": category,
                            "media_category": media_category,
                            "media_category_sub":media_category_sub
                        }
                    )
                                                            
    
    def parse_category_news_list(self, response):
        """카테고리별 뉴스 목록 페이지 확인 함수"""

        # print(f"\nurl: {response.url}")
        
        category = response.meta["media_code"]
        media_category = response.meta["media_category"]
        media_category_sub = response.meta["media_category_sub"]
        # print(f"카테고리 코드: {category}")
        # print(f"카테고리 대분류: {media_category}")
        # print(f"카테고리 소분류: {media_category_sub}")
        
        # if "MID" in response.url:
        #     # 페이지 처리
        #     if response.url == "https://www.etoday.co.kr/"+ category:
        #         page_num = 1
        #     else:
        #         page_num = (response.url).split('=')[-1]
        #     print(f"\n 페이지 번호: {page_num}")
        # else:
        #     print("페이지가 있으면 오류가 난다!!!!!!!!!!!!!")
        #     response.url = "https://www.etoday.co.kr/"+ category
        # print(f"\n 뉴스 목록 url: {response.url}")
        
            
        # 목록 확인
        is_next_news_list = False

        for news_list in response.xpath("//ul[@id='list_W']/li"):
            # print(f"\n리스트 요소: {news_list}")
            
            # 날짜 확인
            date = news_list.xpath("//div[@class='cluster_text_press21']/text()").get()
            # print(f"\n날짜: {date}")
            
            date = datetime.strptime(date, "%Y-%m-%d %H:%M")
            # print(f"datetime 날짜: {date}")
            
            # 입력한 날짜의 기간 범위에 포함되는지 확인
            if self.start_date <= date <= self.end_date:
                # print(f"\n 뉴스 리스트 url: {response.url}")
                # print(f"뉴스 날짜: {date}")
                
                # print(category)
                # if "MID" in category:
                #     is_next_news_list = True
                # else:
                #     is_next_news_list = False
                
                # 뉴스 링크
                category_news_post_url = self.main_url + news_list.xpath("div/div/a/@href").get()
                # print(f"뉴스 링크: {category_news_post_url}")
                
                yield scrapy.Request(
                    
                    # 뉴스 기사 링크
                    url=category_news_post_url,
                    
                    headers=self.headers,
                    
                    # 뉴스 페이지 항목 추출 함수로 연결
                    callback=self.parse_category_news_post,
                    meta={
                        
                        # 날짜
                        "date": date,
                        "media_code": category,
                        "media_category": media_category,
                        "media_category_sub":media_category_sub
                    }
                )
            elif self.end_date < date:
                is_next_news_list = True
                
        # 다른 뉴스 목록을 더 살펴보아야 하는 경우
        if is_next_news_list:
            next_page_num = int(self.page_num)+self.page_request_range
            # print(f"다음 페이지 번호: {next_page_num}")
            yield scrapy.Request(
                
                # 카테고리 뉴스 목록 url
                url=self.category_news_list_url.format(self.total_category, str(next_page_num)),
                
                headers=self.headers,
                
                # 카테고리별 뉴스 목록 페이지 확인 함수로 연결
                callback=self.parse_category_news_list,
                meta={
                        "media_code": category,
                        "media_category": media_category,
                        "media_category_sub":media_category_sub
                } 
            )

    def parse_category_news_post(self, response):
        """뉴스 페이지 항목 추출 함수"""
        
        print(f"\n 기사 링크: {response.url}")
        
        item = SelfStudyScrapyItem()
    
        
        # 언론사 카테고리 대분류
        item["media_category"] = response.meta["media_category"]
        print(f" 기사 카테고리 대분류: {item["media_category"]}")
        
        # 언론사 카테고리 소분류
        item["media_category_sub"] = response.meta["media_category_sub"]
        print(f" 기사 카테고리 소분류: {item["media_category_sub"]}")
        
        # 기사 날짜
        item["inp_date"] = response.meta["date"]
        print(f" 기사 날짜: {item["inp_date"]}")
        
        # 기사 제목
        item["title"] = response.xpath("//section[@class='news_dtail_view_top_wrap']/h1/text()").get().strip()
        print(f" 기사 제목: {item["title"]}")
        
        # 기사 내용
        subheading = " ".join(response.xpath("//section[@class='subview_title']/text()").getall()).strip()
        # print(f" 기사 소제목: {subheading}")
        content = " ".join(response.xpath("//div[@class='articleView']/p/text()").getall()).replace("\n", "")    
        # print(f" 기사 내용: {content}")
        keyword = " ".join(response.xpath("//div[@class='kwd_tags']/a/text()").getall()).replace("\\", "").strip()
        # print(f" 기사 키워드: {keyword}")
        
        item["content"] = subheading + " " + content + " " + keyword
        item["content"] = item["content"].replace("\n", "").replace("\r", "").replace("\\", "").strip()
        print(f" 기사 본문: {item["content"]}")
        print("------------------------------------")
        
        # 핀인사이트 카테고리 대분류
        item["category"] = ""
        # 핀인사이트 카테고리 소분류
        item["category_sub"] = ""
        
        item["save_method"] = self.save_method
        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language

        yield item


#  vscode의 파이썬 Extension으로 디버깅을 하기 위한 세팅입니다.
if __name__ == "__main__":
    settings = get_project_settings()
    settings["LOG_LEVEL"] = "DEBUG"
    settings["ITEM_PIPELINES"] = {
        "crawler_news.pipelines.CrawlerNewsPipeline":300
    }
    process = CrawlerProcess(settings=settings)
    process.crawl(Stella1Spider)
    process.start()