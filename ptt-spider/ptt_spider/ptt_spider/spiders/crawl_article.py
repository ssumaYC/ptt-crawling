# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ptt_spider.settings import REDIS_HOST
from datetime import datetime as dt
from datetime import date
from redis import Redis


class CrawlArticleSpider(CrawlSpider):
    name = 'crawl_article'
    allowed_domains = ['www.ptt.cc']
    start_urls = ['http://www.ptt.cc/']
    r = Redis(host=REDIS_HOST)

    rules = (
        Rule(LinkExtractor(allow=r'cls/\d+'), callback='parse_item', follow=True),
        Rule(LinkExtractor(allow=r'bbs/[\w\-]+/index.html'), callback='parse_article_list', follow=True),
    )

    # def __init__(self, start='', end='', job_id='', **kwargs):
        # super().__init__(**kwargs)
        # self.validate_start_and_end(start, end)
        # self.check_and_init_job_id(job_id)

    def validate_start_and_end(self, start, end):
        if start == '' or end == '':
            raise RuntimeError('start or end is missing')
        else:
            try:
                start = dt.strptime(start, "%Y%m%d").date()
                end = dt.strptime(end, "%Y%m%d").date()
            except ValueError:
                raise ValueError('start and end should be like "20180521"')
        if start > end:
            raise RuntimeError('start date after end date')
        self.start = start
        self.end = end

    def check_and_init_job_id(self, job_id):
        if job_id == "":
            raise ValueError("please provide job_id")
        if self.r.exists(job_id):
            raise RuntimeError('job_id duplicate')
        else:
            self.r.sadd(job_id, 'init_job_id')

    def parse_article_list(self, response):
        if self.is_asking_over18(response):
            payload = {
                'from': response.xpath('//input/@value').get(),
                'yes': response.xpath('//button/@value').get()
            }
            return scrapy.http.FormRequest(
                url='https://www.ptt.cc/ask/over18',
                method="POST",
                formdata=payload,
                callback=self.parse_article_list
            )
        else:
            pass


    def is_asking_over18(self, response):
        return True if response.css('div.over18-notice') != [] else False

    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item

