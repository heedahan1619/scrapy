# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
"""아이템을 처리하고 저장하는데 사용되는 클래스 정의"""
from itemadapter import ItemAdapter


class SelfStudyScrapyPipeline:
    def process_item(self, item, spider):
        return item
