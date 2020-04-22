# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Identity
from w3lib.html import remove_tags
import re


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


def extract_content(text):
    # If the article is a reply of other article the content of the
    # original article will be warpped in <span> so we need to

    # first remove all the div tag and the text been wrapped
    regex = re.compile(r"<div [^>]*>[\w\W]*?</div>")
    text = regex.sub("", text)
    # then remove the span tag only remain the text been wrapped
    text = remove_tags(text)
    return text


class PttArticleItemLoader(ItemLoader):
    # the clean and transform process of certain fields
    default_output_processor = TakeFirst()
    authorId_in = MapCompose(lambda text: text.split(" ")[0])
    authorName_in = MapCompose(lambda text: text.split(" ")[1][1:-1])
    publishedTime_in = MapCompose(lambda dt: int(dt.timestamp() * 1000))
    content_in = MapCompose(extract_content)
    comments_out = Identity()
