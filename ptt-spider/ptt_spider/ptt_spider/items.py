# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose
from w3lib.html import remove_tags
import re


class PttSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class PttArticleItem(scrapy.Item):
    authorId = scrapy.Field()
    authorName = scrapy.Field()
    title = scrapy.Field()
    publishedTime = scrapy.Field()
    content = scrapy.Field()
    canonicalUrl = scrapy.Field()
    createdTime = scrapy.Field()
    updateTime = scrapy.Field()
    comments = scrapy.Field()

def clean_text(text):
    t = remove_tags(text)
    t = t.replace("\xa0", "")
    t = t.strip()
    return t

class PttArticleItemLoader(ItemLoader):

    default_output_processor = TakeFirst()
    authorId_in = Compose(lambda l: l[0].split(" ")[0])
    authorName_in = Compose(lambda l: l[0].split(" ")[1][1:-1])
