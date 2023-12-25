import datetime

import scrapy
from items import SelfStudyScrapyItem

class NewsSpider(scrapy.Spider):
    
    # 스파이더 이름
    name = "news"    
    
    # 언론사
    origin_media = "아주경제(AjuNews)"
    
    language = "ko" 
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    # 메인 홈페이지 url
    url = "https://www.ajunews.com"
    
    # 카테고리 뉴스 목록 url
    category_news_list_url = "https://www.ajunews.com/{}?page={}"
    
    # 페이지 요청 범위
    page_request_range = 10

    def __init__(
            self, 
                                    
            # 날짜 지정
            start_date = "2023-12-01", 
            end_date = "2023-12-22",
            
            # 날짜 입력
            start_date_input = None,
            end_date_input = None,
            
            # # 카테고리 입력
            # user_input_category = None,
            
            save_method="json"
        ):
        
        # 날짜 지정
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
        # # # 날짜 입력
        # # if start_date_input is None:
        # #     start_date_input = input("시작 날짜 입력(YYYYMMDD): ")
        # # if end_date_input is None:
        # #     end_date_input = input("종료 날짜 입력(YYYYMMDD): ")
            
        # # # 날짜 변환 및 유효성 확인
        # # def transform_date(date_input):
        # #     try:
        # #         return datetime.strptime(date_input, "%Y%m%d")
        # #     except ValueError:
        # #         print("올바른 날짜 형식이 아닙니다.")
        # #         return None

        # # # 날짜 datetime 형태 변환
        # # def transform_date_output(date):
        # #     return date.strftime("%Y-%m-%d")
        
        # # self.start_date_input = start_date_input
        # # self.start_date_input = end_date_input
        # self.start_date = transform_date(start_date_input)
        # self.end_date = transform_date(end_date_input) + timedelta(days=1) - timedelta(seconds=1)

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
        return [
            scrapy.Request(
                
                # 메인 홈페이지로 이동
                url=self.url,
                
                headers=self.headers,
                
                # 언론사 카테고리 추출 함수로 연결
                callback=self.parse_media_category
            )
        ]


    def parse_media_category(self, response):   
        """언론사 카테고리 추출 함수"""
        
        # 언론사명
        media = str(self.origin_media.split("(")[0])
        # print(f"언론사: {media}")
        
        # total_category_list = []
        # media_category_dict = {}
        # media_category_sub_dict = {}
        
        """전체 카테고리 수집"""
        
        total_category_list = []
        media_total_category_dict = {}
        media_category_dict = {}
        media_category_sub_dict = {}
        
        dl_elements = response.xpath("//ul[@class='all clearfix']//dl")
        # print(f"\n dl 요소 전체: {dl_elements}")
        # print(f"\n dl 요소 개수: {len(dl_elements)}")
        
        for i, dl in enumerate(dl_elements):
            # print(f"\n dl 인덱스: {i}")
            # print(f"\n dl 요소: {dl}")
            
            """언론사 대분류"""
            # 대분류 카테고리 코드
            dt_href = dl.xpath("dt/a/@href").get()
            dt_split = dt_href.split("/")[3:]
            print(f"\n dt 요소 split: {dt_split}")
            if len(dt_split) > 2:
                dt_code = dt_split[0] + "/" + dt_split[1]
            else:
                dt_code = dt_split[0]
            total_category_list.append(dt_code)
            # print(f"\n dt 코드: {dt_code}")
            
            # 대분류 카테고리 이름
            dt_text = dl.xpath("dt/a/text()").get()
            # print(f"\n dt 이름: {dt_text}")
            
            # 대분류 카테고리 dict
            media_category_dict[dt_code] = dt_text
            print(f"\n {media} 대분류 카테고리 dict: {media_category_dict}")
            
            """언론사 소분류"""
            dd_split = dl.xpath("dd/a/@href").get().split("/")[3:]
            # print(f"\n dd_split: {dd_split}")
            # print(f"\n dd_split 개수: {len(dd_split)}")
            
            if len(dd_split) == 3:
                dd_code = dd_split[0] + "/" + dd_split[1] + "/" + dd_split[2]
            elif len(dd_split) == 2:
                dd_code = dd_split[0] + "/" + dd_split[1]
            else:
                dd_code = dd_split[0]
            total_category_list.append(dd_code)
            print(f"\n dd 코드: {dd_code}")
            
            dd_text = dl.xpath("dd/a/text()").get()
            print(f"\n dd 이름: {dd_text}")
            
            media_category_sub_dict[dd_code] = dd_text
            print(f"\n {media} 소분류 카테고리 dict: {media_category_sub_dict}")
            
        """언론사 전체 카테고리"""
        # 전체 카테고리 리스트
        for category_key in media_category_dict.keys():
            total_category_list.append(category_key)
        for category_sub_key in media_category_sub_dict.keys():
            total_category_list.append(category_sub_key)
        # print(f"\n 전체 카테고리 list: {total_category_list}")
      
        # 전체 카테고리 딕셔너리
        total_category_list_dict = {**media_category_dict, **media_category_sub_dict}
        # print(f"\n 전체 카테고리 dict: {total_category_list_dict}")

        for total_category in total_category_list:
            for page_num in range(1, self.page_request_range+1):
                yield scrapy.Request(
                    
                    # 카테고리 뉴스 목록 url
                    url=self.category_news_list_url.format(total_category, page_num),
                    
                    headers=self.headers,
                    
                    # 카테고리별 뉴스 목록 페이지 확인 함수로 연결
                    callback=self.parse_category_news_list,
                    
                    meta={
                        
                            # 카테고리 대분류
                            "media_category": media_category_code,
                            
                            # 카테고리 소분류
                            "media_category_sub": media_category_sub_code
                            
                        }
                )
    
    
    def parse_category_news_list(self, response):
        """카테고리별 뉴스 목록 페이지 확인 함수"""
        
        # 카테고리 대분류
        media_category = response.meta["media_category"]
        # print(f"\n 카테고리 대분류: {media_category}")
        
        # 카테고리 소분류
        media_category_sub = response.meta["media_category_sub"]
        # print(f"\n 카테고리 소분류: {media_category_sub}")
        
        # 페이지 처리
        if response.url == "https://www.ajunews.com/"+ media_category:
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
                        
                        # 날짜
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
                
                # 카테고리 뉴스 목록 url
                url=self.category_news_list_url.format(self.total_category, str(next_page_num)),
                
                headers=self.headers,
                
                # 카테고리별 뉴스 목록 페이지 확인 함수로 연결
                callback=self.parse_category_news_list,
                meta={
                        "media_category": media_category,
                        "media_category_sub": media_category_sub
                } 
            )

    def parse_category_news_post(self, response):
        """뉴스 페이지 항목 추출 함수"""
        
        print(f"\n 기사 링크: {response.url}")
        
        item = SelfStudyScrapyItem()
        
        # 언론사 카테고리 대분류
        item["media_category"] = response.meta["media_category"]
        # print(f" 기사 카테고리 대분류: {item["media_category"]}")
        
        # 언론사 카테고리 소분류
        item["media_category_sub"] = response.meta["media_category_sub"]
        # print(f" 기사 카테고리 소분류: {item["media_category"]}")
        
        # 기사 날짜
        item["inp_date"] = response.meta["date"]
        print(f" 기사 날짜: {item["inp_date"]}")
        
        # 기사 제목
        item["title"] = response.xpath("//div[@class='view']/article/div[@class='inner']/h1/text()").get().strip()
        print(f" 기사 제목: {item["title"]}")
        
        # 기사 내용
        subheading = " ".join(response.xpath("//div[@class='inner']/section/ul[@class='sub_title']/li/h2/text()").getall()).strip()
        # print(f" 기사 소제목: {subheading}")
        content = " ".join(response.xpath("//div[@id='articleBody']//div/text() | //div[@id='articleBody']/text()[not(parent::p[@class='copy']) and not(self::br)]").getall()).replace("\n", "")    
        # print(f" 기사 내용: {content}")
        keyword = " ".join(response.xpath("//ul[@class='keyword_box']/li/a/text()").getall()).strip()
        # print(f" 기사 키워드: {keyword}")
        
        item["content"] = subheading + " " + content + " " + keyword
        item["content"] = item["content"].replace("\n", "").replace("\r", "").replace("\\", "").strip()
        print(f" 기사 내용: {item["content"]}")

        
        # 핀인사이트 카테고리 대분류
        item["category"] = ""
        # 핀인사이트 카테고리 소분류
        item["category_sub"] = ""
        
        item["save_method"] = self.save_method
        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language

        yield item
