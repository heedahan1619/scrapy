from datetime import datetime, timedelta

import re
import os
import sys
import scrapy
from items import SelfStudyScrapyItem

class CategoryInputSpider(scrapy.Spider):
    
    """스파이더 설정"""
    # 스파이더 이름
    name = "category_input"    
    
    """언론사"""
    # 언론사
    origin_media = "아주경제(AjuNews)"
    
    # 언론사명
    media = str(origin_media.split("(")[0])
    
    language = "ko" 
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    """url"""
    # 메인 홈페이지 url
    main_url = "https://www.ajunews.com"
    
    # 카테고리 뉴스 목록 url
    category_news_list_url = "https://www.ajunews.com/{}?page={}"
    
    # 페이지 요청 범위
    page_request_range = 10
    
    """언론사 카테고리"""
    media_dict = {} # 전체 카테고리 dict 
    media_category_dict = {} # 대분류 카테고리 dict
    

    def __init__(
            self, 
            
            # 날짜 입력
            start_date_input = None,
            end_date_input = None,
            
            save_method="json"
        ):

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
        
        self.save_method = save_method
        assert self.save_method in ("json"), "선택할 수 있는 save_method가 아닙니다."


    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드"""

        print("\n")  
        print(f"언론사: {self.media}")
        print("\n")  
        
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
        
        input_media_category = ""
        
        for category_info in response.xpath("//ul[@class='all clearfix']//dl"):
            
            """카테고리 대분류"""
            for category in category_info.xpath("dt/a"):
                            
                # 대분류 카테고리 코드
                dt_split = category.xpath("@href").get().split("/")[3:]
                if len(dt_split) > 1:
                    media_category_code = dt_split[0] + "/" + dt_split[1]
                else:
                    media_category_code = dt_split[0]
                # print(f"대분류 카테고리 코드: {media_category_code}")
                
                # 대분류 카테고리 이름 
                media_category = category.xpath("text()").get()
                input_media_category += (media_category + " ")
                # print(f"대분류 카테고리: {media_category}")
                
                # 대분류 카테고리 dict
                self.media_category_dict[media_category] = media_category_code
            
                
            # 소분류 카테고리 딕셔너리 초기화
            media_category_sub_dict = {}
                
            """카테고리 소분류"""
            for category_sub in category_info.xpath("dd/a"):
                
                # 소분류 카테고리 이름   
                media_category_sub = category_sub.xpath("text()").get()
                # print(media_category_sub)
                
                # 소분류 카테고리 코드
                dd_split = category_sub.xpath("@href").get().split("/")[3:]
                if len(dd_split) == 3:
                    media_category_sub_code = dd_split[0] + "/" + dd_split[1] + "/" + dd_split[2]
                elif len(dd_split) == 2:
                    media_category_sub_code = dd_split[0] + "/" + dd_split[1]
                else:
                    media_category_sub_code = dd_split[0]
                # print(media_category_sub_code)
                
                # 소분류 카테고리 딕셔너리
                media_category_sub_dict[media_category_sub_code] = media_category_sub
                # print(media_category_sub_dict)
                
            """for문 밖 출력 확인"""
            # 대분류 카테고리를 key로 하고, 소분류 카테고리 정보를 value로 하는 media_dict
            self.media_dict[media_category] = media_category_sub_dict
        # print(f"전체 카테고리 dict: {self.media_dict}")
        # print(f"대분류 카테고리 dict: {self.media_category_dict}")
        
        """카테고리 입력"""
        # 카테고리 입력 시 카테고리 정보 제공을 위한 문자열
        input_media_category = input_media_category[:-1]
        # print(f"선택할 카테고리 문자열: {self.input_category}")

        # 카테고리 선택
        select_media_category = input(f"\n[{input_media_category}] 중에서 카테고리를 선택하세요: \t").split(" ")
        # print(f"선택한 카테고리 전체:  {select_media_category}")
        
        # 선택한 카테고리의 존재 여부 확인
        selected_media_category_list = []
        
        for selected_media_category in select_media_category:
            
            # print(f"선택한 카테고리:  {selected_media_category}")
            # print(f"선택한 카테고리의 존재 여부:  {selected_media_category in input_media_category}")
            if selected_media_category not in  input_media_category:
                print("존재하지 않는 카테고리입니다.")
                select_media_category = input(f"\n[{input_media_category}] 중에서 카테고리를 선택하세요: \t").split(" ")
                selected_media_category_list = select_media_category
            else:
                selected_media_category_list.append(selected_media_category)
            # print(f"선택한 카테고리 list:  {selected_media_category_list}")
    
        
        for selected_media_category in selected_media_category_list:
            # print(f"선택한 카테고리:  {selected_media_category}")
            
            # 선택한 카테고리의 소분류 dict 확인    
            selected_media_category_sub_dict = self.media_dict[selected_media_category]
            # print(f"\n선택한 카테고리의 소분류 dict: {selected_media_category_sub_dict}")

            """선택한 카테고리에 해당하는 뉴스 목록 확인"""    
            # 뉴스 목록 확인
            for selected_media_category_sub_code, selected_media_category_sub in selected_media_category_sub_dict.items():
                # print(f"선택한 카테고리의 소분류 코드 : {selected_media_category_sub_code}")
                # print(f"선택한 카테고리의 소분류 : {selected_media_category_sub}")
                
                # 페이지 지정
                for page_num in range(1, self.page_request_range+1):
                    
                    # 스크래피 요청
                    yield scrapy.Request(
                        
                        # 카테고리 뉴스 목록 url
                        url = self.category_news_list_url.format(selected_media_category_sub_code, page_num),
                        
                        headers=self.headers,
                        
                        # 카테고리별 뉴스 목록 페이지 확인 함수로 연결
                        callback=self.parse_category_news_list,
                        
                        meta={
                            "media_category": selected_media_category,
                            "media_category_sub": selected_media_category_sub,
                            "media_category_sub_code": selected_media_category_sub_code 
                        }
                    )
        
    
    def parse_category_news_list(self, response):
        """카테고리별 뉴스 목록 페이지 확인 함수"""

        # print(f"선택한 카테고리 뉴스 목록 url: {response.url}")

        media_category = response.meta["media_category"]
        media_category_sub = response.meta["media_category_sub"]
        media_category_sub_code = response.meta["media_category_sub_code"]
        # print(f"{self.media} 카테고리 대분류: {media_category}")
        # print(f"{self.media} 카테고리 소분류: {media_category_sub}")
        # print(f"{self.media} 카테고리 소분류 코드: {media_category_sub_code}")

        # 페이지 처리
        if response.url == "https://www.ajunews.com/"+ media_category_sub_code:
            page_num = 1
        else:
            page_num = (response.url).split('/')[-1]
        # print(f"\n 뉴스 목록 url: {response.url}")
            
        # 목록 확인
        is_next_news_list = False
        for news_list in response.xpath("//ul[@class='news_list']/li/div[@class='text_area']"):
            
            # 날짜 확인
            date_elements = news_list.xpath("ul[@class='date']/li/text()").getall()
            date = date_elements[0] + " " + date_elements[1]
            # print(f"날짜: {date}")
            
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            # print(f"datetime 날짜: {date}")
            
            # 입력한 날짜의 기간 범위에 포함되는지 확인
            if self.start_date <= date <= self.end_date:
                # print(f"\n 뉴스 리스트 url: {response.url}")
                # print(f"뉴스 날짜: {date}")
                
                is_next_news_list = True
                
                # 뉴스 링크
                category_news_post_url = "https:" + news_list.xpath("a[@class='tit']/@href").get()
                # print(f"뉴스 링크: {category_news_post_url}")
                
                yield scrapy.Request(
                    
                    # 뉴스 링크
                    url=category_news_post_url,
                    
                    headers=self.headers,
                    
                    # 뉴스 페이지 항목 추출 함수로 연결
                    callback=self.parse_category_news_post,                    
                    meta={
                        "date": date,
                        "media_category": media_category,
                        "media_category_sub": media_category_sub,
                        "media_category_sub_code": media_category_sub_code 
                    }
                )
            elif self.end_date < date:
                is_next_news_list = True
                
        # 다른 뉴스 목록을 더 살펴보아야 하는 경우
        if is_next_news_list:
            next_page_num = int(page_num)+self.page_request_range
            # print(f"다음 페이지 번호: {next_page_num}")
            yield scrapy.Request(
                
                # 카테고리 뉴스 목록 url
                url=self.category_news_list_url.format(self.media_category_sub_code, str(next_page_num)),
                
                headers=self.headers,
                
                # 카테고리별 뉴스 목록 페이지 확인 함수로 연결
                callback=self.parse_category_news_list,
                meta={
                        "media_category": media_category,
                        "media_category_sub": media_category_sub,
                        "media_category_sub_code": media_category_sub_code 
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
        item["title"] = response.xpath("//div[@class='view']/article/div[@class='inner']/h1/text()").get().strip()
        print(f" 기사 제목: {item["title"]}")
        
        # 기사 내용
        subheading = " ".join(response.xpath("//div[@class='inner']/section/ul[@class='sub_title']/li/h2/text()").getall()).strip()
        # print(f" 기사 소제목: {subheading}")
        content = " ".join(response.xpath("//div[@id='articleBody']//div/text() | //div[@id='articleBody']/text()[not(parent::p[@class='copy']) and not(self::br)]").getall()).replace("\n", "").strip() 
        # print(f" 기사 내용: {content}")
        keyword = " ".join(response.xpath("//ul[@class='keyword_box']/li/a/text()").getall()).replace("\n", "").strip() 
        # print(f" 기사 키워드: {keyword}")
        
        item["content"] = subheading + " " + content + " " + keyword
        # item["content"] = item["content"].replace("\n", "").replace("\r", "").replace("\\", "").strip()
        print(f" 기사 내용: {item["content"]}")
        print("--------------------------------")
        
        # 핀인사이트 카테고리 대분류
        item["category"] = ""
        # 핀인사이트 카테고리 소분류
        item["category_sub"] = ""
        
        item["save_method"] = self.save_method
        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language

        yield item

