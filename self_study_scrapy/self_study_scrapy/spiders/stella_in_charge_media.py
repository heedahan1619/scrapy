import re
import os
import sys
import scrapy
import json
from datetime import datetime, timedelta
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from items import CrawlerNewsItem

# 정규표현식 불러와서 적용
import preprocess.constants as cs
import preprocess.news_regex as nr

class StartupDailySpider(scrapy.Spider):
    name = "startupdaily"    # spider name
    origin_media = "스타트업데일리(StartupDaily)"
    language = "ko" # ko, en
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    news_url = "https://www.startupdaily.kr"
    news_list_url_total = "https://www.startupdaily.kr/news/articleList.html?page={}&sc_section_code={}"
    news_list_url_total_regex = re.compile(r"https://www.startupdaily.kr/news/articleList.html\?page=")
    page_request_range = 10

    # 카테고리 호환작업에 쓸 json 파일 불러오기
    media_name_regex = re.compile(r"\(.*\)")
    media_kor_name = re.sub(media_name_regex, "", origin_media)
    with open("../preprocess/news_category.json", "r", encoding="utf-8") as f:
        category_compatible_dict = json.load(f)
    category_compatible_dict = category_compatible_dict[media_kor_name]
    print(f"category_compatible_dict : {category_compatible_dict}")

    def __init__(
            self,
            start_date="2022-01-01", # 2022-01-01, 2023-11-01
            end_date="2022-02-28", # 2022-02-28, 2024-01-05
            save_method="json"
        ):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        assert self.start_date.timestamp() <= self.end_date.timestamp(), "end_date이 start_date보다 앞에 있습니다."
        self.save_method = save_method
        assert self.save_method in ("json"), "선택할 수 있는 save_method가 아닙니다."

    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드입니다.
        """
        return [
            scrapy.Request(
                url=self.news_url,
                headers=self.headers,
                callback=self.parse_menu_list
            )
        ]
    
    def parse_menu_list(self, response):
        """뉴스 사이트 탭 메뉴를 가져옵니다.
        """
        news_menu_list = response.xpath("//nav[@id='allService']/ul/li/a/text()").getall()[1:]
        print(f"news_menu_list : {news_menu_list}")
        news_menu_list
        # # README.md 파일 내 카테고리 목록에 기입
        # for news_menu in news_menu_list:
        #     print(news_menu, end=", ")
        news_menu_list_code = response.xpath("//nav[@id='allService']/ul/li/a/@href").getall()[1:]
        news_menu_list_code = [i.split("=")[1].split("&")[0] for i in news_menu_list_code]
        # # 한 개 지우는 경우
        # del news_menu_list_code[news_menu_list.index('채용 정보')]
        # del news_menu_list[news_menu_list.index('채용 정보')]
        # 두 개 이상 지우는 경우
        for i in ['채용 정보', '지원사업']:
            del news_menu_list_code[news_menu_list.index(i)]
            del news_menu_list[news_menu_list.index(i)]
        # print(f"news_menu_list : {news_menu_list}")        
        # print(f"news_menu_list_code : {news_menu_list_code}"
        
        global news_menu_dict
        news_menu_dict = dict(zip(news_menu_list, news_menu_list_code))
        news_menu_dict_opp = dict(zip(news_menu_list_code, news_menu_list))
        news_menu_list += ["all"]

        news_menu_select = input(f"{news_menu_list} 중에서 선택(다중 선택 시 (띄어쓰기))로 구분): ").split(" ")
        if news_menu_select==["all"]:
            news_menu_select_code = list(news_menu_dict_opp.keys())
        else:
            news_menu_select_code = [news_menu_dict[i] for i in news_menu_select]
        # print(f"news_menu_select : {news_menu_select}")
        # print(f"news_menu_select_code : {news_menu_select_code}")
        
        
        print(f"Crawling... : {news_menu_select}")
        for i in news_menu_select_code:
            print(news_menu_dict_opp[i])
            for j in range(1, self.page_request_range+1):
                yield scrapy.Request(
                    url=self.news_list_url_total.format(str(j), i),
                    headers=self.headers,
                    callback=self.parse_news_list,
                    meta={
                            "media_category": news_menu_dict_opp[i]
                        }
                )

    def parse_news_list(self, response):
        """뉴스 목록 페이지를 분석합니다.
        """
        # print(f"url: {response.url}")
        media_category = response.meta["media_category"]
        media_category_sub = response.meta["media_category"]
        print(f"media_category: {media_category}")
        print(f"media_category_sub: {media_category_sub}")
        if response.url == f"https://www.startupdaily.kr/news/articleList.html?sc_section_code={news_menu_dict[media_category]}":
            page_num = 1
        else:
            page_num = re.sub(self.news_list_url_total_regex, "", response.url)
            page_num = page_num.split('&')[0]
            
        # 목록 확인
        is_next_news_list = False
        for post_info_date in response.xpath("//section[@id='section-list']/ul/li/div[@class='view-cont']"):
            # 날짜 확인
            date = post_info_date.xpath("span[@class='byline']/em[@class='replace-date']/text()").get()
            date = datetime.strptime(date, "%Y.%m.%d %H:%M")                           
            if self.start_date <= date <= self.end_date:
                is_next_news_list = True
                link = post_info_date.xpath("h4[@class='titles']/a/@href").get()
                link = self.news_url + link
                yield scrapy.Request(
                    url=link,
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
                url=self.news_list_url_total.format(str(next_page_num), news_menu_dict[media_category]),
                headers=self.headers,
                callback=self.parse_news_list,
                meta={
                    "media_category": media_category,
                    "media_category_sub": media_category_sub
                } 
            )

    def parse_news_page(self, response):

        item = CrawlerNewsItem()
        
        item["save_method"] = self.save_method
        item["inp_date"] = response.meta["date"]
        
        # 핀인사이트 카테고리 대분류, 소분류 출력
        change_category = self.category_compatible_dict[response.meta["media_category"]]
        if list(change_category.keys())[0]=="all":
            item["category"] = change_category["all"][0]
            item["category_sub"] = change_category["all"][1]
        else:
            change_category = change_category[response.meta["media_category_sub"]]
            item["category"] = change_category[0]
            item["category_sub"] = change_category[1]

        # 언론사 카테고리 대분류, 소분류 출력
        item["media_category"] = response.meta["media_category"]
        item["media_category_sub"] = response.meta["media_category_sub"]

        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language

        # 뉴스 제목 추출
        item["title"] = response.xpath("//h3[@class='heading']/text()").get().strip()
        item["title"] = item["title"].translate(str.maketrans("‘’“”∼–×․", "''\"\"~-x.", "\r\n\xa0\t"))

        # 뉴스 본문 추출
        item["content"] = " ".join(response.xpath("//div[@class='article-body']/article/p/text()"
        ).getall()).replace("\n", "").strip()
        item["content"] = item["content"].translate(str.maketrans("‘’“”∼–×․\xa0", "''\"\"~-x. ", "\r\n\t"))
        pattern = re.compile("|".join(cs.WHITESPACE + cs.PARENTHESIS + cs.SPECIAL_CHAR))
        item["content"] = re.sub(pattern, " ", item["content"])
        pattern = re.compile("|".join(nr.REGEX_PATTERN[self.name] + nr.REGEX_PATTERN["COMMON"]))
        item["content"] = re.sub(pattern, "", item["content"]).strip()

        # 항목 출력
        print(f"\nurl: {item['origin_url']}")
        print(f"inp_date: {item['inp_date']}")        
        print(f"category: {item['category']}")
        print(f"category_sub: {item['category_sub']}")
        print(f"media_category: {item['media_category']}")
        print(f"media_category_sub: {item['media_category_sub']}")
        print(f"title: {item['title']}")
        print(f"content: {item['content']}")

        yield item


#  vscode의 파이썬 Extension으로 디버깅을 하기 위한 세팅입니다.
if __name__ == "__main__":
    settings = get_project_settings()
    settings["LOG_LEVEL"] = "DEBUG"
    settings["ITEM_PIPELINES"] = {
        "crawler_news.pipelines.CrawlerNewsPipeline":300
    }
    process = CrawlerProcess(settings=settings)
    process.crawl(StartupDailySpider)
    process.start()