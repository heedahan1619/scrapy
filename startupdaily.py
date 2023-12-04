from datetime import datetime

import re
import os
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from items import CrawlerNewsItem

class StartupDailySpider(scrapy.Spider):
    """예시로 작성된 언론사 스타트업 데일리(StartupDaily)의 spider입니다.
    """
    name = "startupdaily"    # spider name
    origin_media = "스타트업 데일리(StartupDaily)"
    language = "ko" # ko, en
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
    }
    
    # TODO: startupdaily.kr에는 startup 외에도 뉴스를 분류한 탭이 존재합니다.
    news_list_url_startup = "https://www.startupdaily.kr/news/articleList.html?sc_section_code=S1N1&page={}"
    news_list_url_startup_regex = re.compile(r"https://www.startupdaily.kr/news/articleList.html?sc_section_code=S1N1&page=")
    post_info_date_regex = re.compile(r"\s\d.\d")
    page_request_range = 10

    def __init__(
            self, 
            start_date="2023-10-01",
            end_date="2023-12-02",
            save_method="json"
        ):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        assert self.start_date.timestamp() <= self.end_date.timestamp(), "end_date이 start_date보다 앞에 있습니다."
        self.save_method = save_method
        assert self.save_method in ("json"), "선택할 수 있는 save_method가 아닙니다."

    def start_requests(self):
        """크롤러가 시작하면서 실행하는 메소드입니다.
        """
        return [
            scrapy.Request(
                url=self.news_list_url_startup.format(str(i)),
                headers=self.headers,
                callback=self.parse_news_list,
                meta={
                    "category_sub": "startup"  # 뉴스 탭의 이름을 category_sub로 사용합니다.
                }
            )
            for i in range(1, self.page_request_range+1)
        ]
    
    def parse_news_list(self, response):
        """뉴스 목록 페이지를 분석합니다.
        """
        print(response.url)
        category_sub = response.meta["category_sub"]
        if response.url == "https://www.startupdaily.kr/news/articleList.html?sc_section_code=S1N1&page=":
            page_num = 1
        else:
            page_num = re.sub(self.news_list_url_startup_regex, "", response.url)
        # 목록 확인
        is_next_news_list = False
        for post_info_content in response.xpath("//div[@class='view-cont']"):
            # 날짜 확인
            date = post_info_content.xpath("span[@class='byline']/em/text()").get()
            date = re.sub(self.post_info_date_regex, "", date)
            date = datetime.strptime(date, "%Y/%m/%d")
            if self.start_date <= date <= self.end_date:
                is_next_news_list = True
                link = post_info_content.xpath("h4[@class='titles']/a/@href").get()
                yield scrapy.Request(
                    url=link,
                    headers=self.headers,
                    callback=self.parse_news_page,
                    meta={
                        "date": date,
                        "category_sub": category_sub
                    }
                )
            elif self.end_date < date:
                is_next_news_list = True
        # 다른 뉴스 목록을 더 살펴보아야 하는 경우
        if is_next_news_list:
            next_page_num = int(page_num)+self.page_request_range
            yield scrapy.Request(
                url=self.news_list_url_startup.format(str(next_page_num)),
                headers=self.headers,
                callback=self.parse_news_list,
                meta={
                    "category_sub": category_sub
                } 
            )

    def parse_news_page(self, response):
        print(f"\t{response.url}")
        item = CrawlerNewsItem()
        item["save_method"] = self.save_method
        item["inp_date"] = response.meta["date"]
        item["category"] = "스타트업"
        item["category_sub"] = response.meta["category_sub"]
        item["origin_nm"] = self.origin_media
        item["origin_url"] = response.url
        item["language"] = self.language
        # (중요) 기사 제목과 본문은 꼭 기사에 대한 내용만 깔끔하게 뽑히는지 확인이 필요합니다.
        # 깔끔하게 뽑히지 않는 경우, replace 메소드나 정규표현식을 사용하여 불필요한 부분을 제거해주세요.
        # 아래와 같이 기사 본문과 관련 없이 지속적으로 등장하는 문구도 꼭 제거해야 합니다.
        # - 연합뉴스TV 기사문의 및 제보 : 카톡/라인 jebo23
        # - 하수영 기자 ha.suyoung@joongang.co.kr
        # - ▼유선희 기자 yu@khan.kr
        # - 플랫팀 기자 flat@kyunghyang.com
        # - 영상취재 강명철
        item["title"] = response.xpath("//header[@class='article-view-header']/h3/text()").get()
        item["content"] = " ".join(response.xpath("//div[@class='article-body']/p/text()").getall()).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("\xa0", " ").replace("&nbsp")
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
