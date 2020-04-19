# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ptt_spider.settings import REDIS_HOST
from datetime import datetime as dt
from datetime import date
from redis import Redis
import requests


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
            return self.form_request_to_article_list(response)
        else:
            pass
        article_hrefs = self.extract_article_hrefs(response)
        oldest_date, newest_date = self.get_oldest_and_newest_date(article_hrefs)
        if oldest_date > self.end:
            return self.form_request_to_previous_list_page(response)
        elif newest_date < self.start:
            return None
        else:
            for href in article_hrefs:
                if r.sismember(self.job_id, bytes(href, 'utf-8')):
                    continue
                else:
                    url = self.get_url_from_href(href)
                    yield scrapy.http.Request(url, callback=self.parse_item)
                    yield self.form_request_to_previous_list_page(response)

    def is_asking_over18(self, response):
        return True if response.css('div.over18-notice') != [] else False

    def form_request_to_article_list(self, response):
        payload = {
            'from': response.xpath('//input/@value').get(),
            'yes': response.xpath('//button/@value').get()
        }
        return scrapy.http.FormRequest(
            url='https://www.ptt.cc/ask/over18',
            method="POST",
            formdata=payload,
            callback=self.parse_article_list,
            dont_filter=True)

    def extract_article_hrefs(self, response):
        rlist = response.css('div.r-list-container').xpath('./div')
        article_hrefs = []
        for r in rlist[1:]:
            if r.xpath('./@class').get() == 'r-list-sep':
                break
            else:
                href = r.css('div.title a::attr(href)').get()
            if href is not None:
                article_hrefs.append(href)
        return article_hrefs

    def get_oldest_and_newest_date(self, hrefs):
        oldest = None
        newest = None
        for i in range(len(hrefs)):
            if oldest is None:
                oldest_date = self.get_article_date(hrefs[i])
            if newest is None:
                newest_date = self.get_article_date(hrefs[(-1 - i)])
            if oldest_date != None and newest_date != None:
                break
        return oldest_date, newest_date

    def get_article_date(self, href):
        resp = requests.get(self.get_url_from_href(href))
        response = scrapy.Selector(resp)
        meta = response.css("div.article-metaline span.article-meta-value::text").getall()
        date = dt.strptime(meta[-1], "%c").date()
        return date

    def form_request_to_previous_list_page(self, response):
        previous_href = response.css('div.btn-group-paging').xpath('./a[2]/@href').get()
        if previous:
            url = self.get_url_from_href(previous_href)
            return scrapy.http.Request(url, callback=self.parse_article_list)

    def get_url_from_href(self, href):
        return "https://" + self.allowed_domains[0] + href

    def parse_item(self, response):
        item = {}
        #item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        #item['name'] = response.xpath('//div[@id="name"]').get()
        #item['description'] = response.xpath('//div[@id="description"]').get()
        return item

