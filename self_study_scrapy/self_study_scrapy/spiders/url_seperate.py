from datetime import datetime, timedelta

import re
import os
import sys
import scrapy
from items import SelfStudyScrapyItem


class SmedailySpider(scrapy.Spider):
    
    """스파이더 설정"""
    name = "smedaily" # 스파이더 이름   
    
    """언론사"""
    origin_media = "중소기업신문(Smedaily)" # 언론사
    media = str(origin_media.split("(")[0]) # 언론사명
    
    language = "ko" 
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    page_request_range = 10 # 페이지 요청 범위
    
    """url"""
    main_url = "https://www.smedaily.co.kr" # 메인 홈페이지 url
    category_news_list_url = "https://www.smedaily.co.kr{}&page={}" # 카테고리 뉴스 목록 url
    
    """언론사 카테고리"""
    media_dict = {} # 언론사 딕셔너리(key는 대분류, value는 소분류 딕셔너리)
    media_category_dict = {} # 언론사 카테고리 대분류 딕셔너리(key는 대분류, value는 대분류 코드)

    def __init__(
            self, 
            save_method="json",
            start_date_input = None, # 시작 날짜 입력
            end_date_input = None # 종료 날짜 입력
        ):
        self.save_method = save_method
        assert self.save_method in ("json"), "선택할 수 있는 save_method가 아닙니다."

        """날짜 입력 기능"""
        if start_date_input is None: # 시작 날짜 입력
            start_date_input = input("시작 날짜 입력(YYYYMMDD): ")
        if end_date_input is None: # 종료 날짜 입력
            end_date_input = input("종료 날짜 입력(YYYYMMDD): ")
            
        def transform_date(date_input): # 날짜 변환 및 유효성 확인 함수
            try:
                return datetime.strptime(date_input, "%Y%m%d")
            except ValueError:
                print("올바른 날짜 형식이 아닙니다.")
                return None

        def transform_date_output(date): # 날짜 datetime 형태 변환 함수
            return date.strftime("%Y-%m-%d")
    
        self.start_date_input = start_date_input
        self.start_date_input = end_date_input
        self.start_date = transform_date(start_date_input)
        self.end_date = transform_date(end_date_input) + timedelta(days=1) - timedelta(seconds=1)

        # start_date와 end_date의 유효성 확인
        assert self.start_date is not None and self.end_date is not None, "유효하지 않은 날짜 형식이 입력되었습니다."
        assert self.start_date.timestamp() <= self.end_date.timestamp(), "end_date가 start_date보다 앞에 있습니다."

    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드"""
        
        print("\n")  
        print(f"언론사: {self.media}")
        print("\n")  
    
        return [
            scrapy.Request(
                url=self.main_url,
                headers=self.headers,
                callback=self.parse_media_category
            )
        ]
        
    def parse_media_category(self, response):   
        """언론사 카테고리 추출 함수"""   

        input_media_category = "" # 카테고리 설명 문자열 초기화

        """언론사 카테고리"""
        for media_elements in response.xpath("//ul[@id='user-menu']/li[@class='secline']"):
        
            """언론사 카테고리 대분류 """
            for media_category_elements in media_elements.xpath("a"):
                media_category = media_category_elements.xpath("text()").get() # 언론사 카테고리 대분류
                input_media_category += (media_category + ", ") # 카테고리 설명 문자열
                media_category_code = media_category_elements.xpath("@href").get() # 언론사 카테고리 대분류 코드
                self.media_category_dict[media_category] = media_category_code # 언론사 카테고리 대분류 딕셔너리
                
            """언론사 카테고리 소분류 """
            media_category_sub_dict = {} # 소분류 카테고리 딕셔너리 초기화
            for media_category_sub_elements in media_elements.xpath("//li[@class='sub']/a"):
                media_category_sub = media_category_sub_elements.xpath("text()").get() # 언론사 카테고리 소분류               
                media_category_sub_code = media_category_sub_elements.xpath("@href").get() # 언론사 카테고리 소분류 코드
                media_category_sub_dict[media_category_sub] = media_category_sub_code # 언론사 카테고리 소분류 딕셔너리
            self.media_dict[media_category] = media_category_sub_dict # 언론사 딕셔너리

        """카테고리 입력"""
        input_media_category = input_media_category[:-2] # 카테고리 설명 문자열
        select_media_category = input(f"\n[{input_media_category}] 중에서 카테고리를 선택하세요: \t").split(", ") # 카테고리 선택
        selected_media_category_list = [] # 선택한 카테고리 리스트
        # 선택한 카테고리의 존재 여부 확인
        for selected_media_category in select_media_category: 
            if selected_media_category not in input_media_category:
                print("존재하지 않는 카테고리입니다.")
                select_media_category = input(f"\n[{input_media_category}] 중에서 카테고리를 선택하세요: \t").split(", ")
                selected_media_category_list = select_media_category
            else:
                selected_media_category_list.append(selected_media_category)
            
        for selected_media_category in selected_media_category_list:
            print(selected_media_category)
            
            """선택한 카테고리에 해당하는 뉴스 목록 확인"""
            if selected_media_category in self.media_dict:
                # 언론사 카테고리 소분류 코드 추출
                for media_category_sub, media_category_sub_code in self.media_dict[selected_media_category].items(): 
                    for page_num in range(1, self.page_request_range+1):
                        yield scrapy.Request(
                            url = self.category_news_list_url.format(media_category_sub_code, page_num),
                            headers=self.headers,
                            callback=self.parse_category_news_list,
                            meta={
                                "media_category": selected_media_category,
                                "media_category_sub": media_category_sub,
                                "media_category_sub_code": media_category_sub_code,
                            }
                        )
                    
    
    def parse_category_news_list(self, response):
        """카테고리별 뉴스 목록 확인 함수"""
        
        media_category = response.meta["media_category"]
        media_category_sub = response.meta["media_category_sub"]
        media_category_sub_code = response.meta["media_category_sub_code"]
        
        """페이지 처리"""
        if response.url == self.main_url + media_category_sub_code:
            page_num = 1
        else:
            page_num = (response.url).split('=')[-1]
        is_next_news_list = True

        """카테고리별 뉴스 목록 확인"""
        is_next_news_list = False
        for news_list in response.xpath("//section[@id='section-list']"):         
            date = news_list.xpath("(//span[@class='byline']/em[3]/text() | //em[@class='info dated']/text())").get() # 날짜 추출              
            date = datetime.strptime(date, "%Y.%m.%d %H:%M") # 날짜 형태 변환

            """입력한 기간 포함 여부 확인"""
            if self.start_date <= date <= self.end_date: # 입력한 기간 내
                is_next_news_list = True
                category_news_post_url = self.main_url + news_list.xpath("//h4[@class='titles']/a/@href").get() # 뉴스 기사 url
                print(category_news_post_url)
                yield scrapy.Request(
                    url=category_news_post_url,
                    headers=self.headers,
                    callback=self.parse_category_news_post, 
                    meta={
                        "date": date,
                        "media_category": media_category,
                        "media_category_sub": media_category_sub,
                        "media_category_sub_code": media_category_sub_code
                    }
                )
            elif self.end_date < date: # 입력한 기간 외
                is_next_news_list = True
                
            # 카테고리별 뉴스 목록의 다음 페이지 확인
            if is_next_news_list == True: 
                next_page_num = int(page_num)+self.page_request_range     
                yield scrapy.Request(
                    url=self.category_news_list_url.format(media_category_sub_code, str(next_page_num)),
                    headers=self.headers,
                    callback=self.parse_category_news_list,  
                    meta={
                        "media_category": media_category,
                        "media_category_sub": media_category_sub,
                        "media_category_sub_code": media_category_sub_code
                    } 
                )   
            

    def parse_category_news_post(self, response):
        """뉴스 페이지 항목 추출 함수"""

        item = SelfStudyScrapyItem()
        
        item["save_method"] = self.save_method
        item["inp_date"] = response.meta["date"] # 기사 날짜
        item["category"] = "" # 핀인사이트 카테고리 대분류
        item["category_sub"] = "" # 핀인사이트 카테고리 소분류  
        item["media_category"] = response.meta["media_category"] # 언론사 카테고리 대분류
        item["media_category_sub"] = response.meta["media_category_sub"] # 언론사 카테고리 소분류
        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language
        item["title"] = response.xpath("//h3[@class='heading']/text()").get().strip() # 기사 제목
        # 기사 내용
        subheading = " ".join(response.xpath("//h4[@class='subheading']/text()[not (self::br)]").getall()).replace("\n", "").strip()
        content = " ".join(response.xpath("//div[@class='article-body']/p/text() | //div[@class='article-body']/article/p/text() | //div[@class='article-body']/article/p/strong/text()").getall()).replace("\n", "").strip()
        keyword = " ".join(response.xpath("//div[@class='tag-group']/a[@class='tag']/text()").getall()).replace("\n", "").strip()
        item["content"] = subheading + " " + content + " " + keyword
        
        print(f"\기사 링크: {response.url}")
        print(f" 기사 카테고리 대분류: {item["media_category"]}")
        print(f" 기사 카테고리 소분류: {item["media_category_sub"]}")
        print(f" 기사 날짜: {item["inp_date"]}")
        print(f" 기사 제목: {item["title"]}")
        print(f" 기사 본문: {item["content"]}")
        print("--------------------------------")
        
        yield item
