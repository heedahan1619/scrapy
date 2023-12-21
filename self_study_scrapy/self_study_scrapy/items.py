# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

"""데이터 모델을 정의하는데 사용되는 아이템 클래스 포함"""

import scrapy


class SelfStudyScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    
    media = scrapy.Field()
    media_url = scrapy.Field()
    category_name = scrapy.Field()
    
