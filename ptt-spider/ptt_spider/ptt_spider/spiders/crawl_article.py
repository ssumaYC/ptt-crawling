# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ptt_spider.settings import REDIS_HOST
from ptt_spider.items import PttArticleItem, PttArticleItemLoader
from datetime import datetime as dt
from redis import Redis
import requests


class CrawlArticleSpider(CrawlSpider):
    name = 'crawl_article'
    allowed_domains = ['www.ptt.cc']
    start_urls = ['https://www.ptt.cc/bbs/index.html']
    r = Redis(host=REDIS_HOST)
    rules = (
        # This rule is telling spider to go into board category list
        # like "https://www.ptt.cc/cls/1"
        Rule(LinkExtractor(allow=r'cls/\d+'), follow=True),
        # this one identify the url of certain board, a list of article
        # then deliver its response to method "parse_article_list"
        Rule(LinkExtractor(allow=r'bbs/[\w\-]+/index.html'),
             callback='parse_article_list', follow=True),
    )

    def __init__(self, start='', end='', job_id='', recover='false', **kwargs):
        super().__init__(**kwargs)
        self.validate_start_and_end(start, end)
        self.check_and_init_job_id(job_id, recover)

    def validate_start_and_end(self, start, end):
        # must provide start and end
        if start == '' or end == '':
            raise RuntimeError('start or end is missing')
        else:
            # check the format of start and end
            try:
                start = dt.strptime(start, "%Y%m%d").date()
                end = dt.strptime(end, "%Y%m%d").date()
            except ValueError:
                raise ValueError('start and end should be like "20180521"')
        # can not start after end
        if start > end:
            raise RuntimeError('start date after end date')
        # start and end is ok to use
        self.start = start
        self.end = end

    def check_and_init_job_id(self, job_id, recover):
        # must provide job_id
        if job_id == "":
            raise ValueError("please provide job_id")
        if recover == 'true':
            # check the job_id provided is exists
            if self.r.exists(job_id):
                self.job_id = job_id
            else:
                raise RuntimeError('job_id not exists')
        elif recover == 'false':
            # check the job_id is not being used
            if self.r.exists(job_id):
                raise RuntimeError('job_id duplicate')
            else:
                self.r.sadd(job_id, 'init_job_id')
            self.job_id = job_id
        else:
            raise RuntimeError('recover only accept "true" or "false"')

    def parse_article_list(self, response):
        # Some board will asking is over 18 or not. If is asking
        # then form a request to get the response of the board
        if self.is_asking_over18(response):
            return self.form_request_to_article_list(response)
        else:
            pass
        # Get the urls of every articles except the 置頂 article
        # Then get the date of the newest article and the oldest article
        # Compare these dates to start and end
        # If the oldest article is after the end then go to the previous page
        # elif newest article is before start means spider have done searching
        # the current board, because spider start from the newsest page list
        # else check is the article url is crawled or not
        # if yes then pass, if no sent request to the url
        # then pass the response to method "parse_item"
        # after iter though the url list just go to the previous page
        # then do the same thing again
        article_hrefs = self.extract_article_hrefs(response)
        article_urls = [self.get_url_from_href(href) for href in article_hrefs]
        oldest_date, newest_date = self.get_oldest_and_newest_date(article_urls)
        if oldest_date > self.end:
            return self.form_request_to_previous_list_page(response)
        elif newest_date < self.start:
            return None
        else:
            for url in article_urls:
                if self.r.sismember(self.job_id, bytes(url, 'utf-8')):
                    continue
                else:
                    yield scrapy.http.Request(url, callback=self.parse_item)
            yield self.form_request_to_previous_list_page(response)

    def is_asking_over18(self, response):
        # check the response is asking over 18 or not
        return True if response.css('div.over18-notice') != [] else False

    def form_request_to_article_list(self, response):
        # form the request to the board response then pass it to method "parse_article_list"
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
            # article below this div is 置頂 article
            if r.xpath('./@class').get() == 'r-list-sep':
                break
            else:
                href = r.css('div.title a::attr(href)').get()
            # some deleted article will not have href
            if href is not None:
                article_hrefs.append(href)
        return article_hrefs

    def get_oldest_and_newest_date(self, urls):
        # get the oldest from the beginning of the urls
        oldest = None
        newest = None
        for i in range(len(urls)):
            if oldest is None:
                oldest_date = self.get_article_date(urls[i])
            if newest is None:
                newest_date = self.get_article_date(urls[(-1 - i)])
            if oldest_date is not None and newest_date is not None:
                break
        return oldest_date, newest_date

    def get_article_date(self, url):
        # the precise article date can only be obtain within the article page
        try:
            resp = requests.get(url)
            response = scrapy.Selector(resp)
            meta_css = "div.article-metaline span.article-meta-value::text"
            meta = response.css(meta_css).getall()
            if meta:
                date = dt.strptime(meta[-1], "%c").date()
            else:
                date = None
        except (TypeError, ValueError):
            date = None
        return date

    def form_request_to_previous_list_page(self, response):
        # form the request for the response of the previous list page
        previous_href = response.css('div.btn-group-paging')\
                                .xpath('./a[2]/@href').get()
        # there may not be previous page
        if previous_href:
            url = self.get_url_from_href(previous_href)
            return scrapy.http.Request(url, callback=self.parse_article_list)

    def get_url_from_href(self, href):
        return "https://" + self.allowed_domains[0] + href

    def parse_item(self, response):
        # check article is between start and end
        publishedDatetime = response.xpath('//div[@id="main-content"]/div[4]/span[2]/text()').get()
        if publishedDatetime is None:
            return None
        publishedDatetime = dt.strptime(publishedDatetime, "%c")
        publishedDate = publishedDatetime.date()
        if publishedDate > self.end or publishedDate < self.start:
            return None
        # locate the target field on the page
        loader = PttArticleItemLoader(item=PttArticleItem(), response=response)
        loader.add_xpath('authorId', '//div[@id="main-content"]/div[1]/span[2]/text()')
        loader.add_xpath('authorName', '//div[@id="main-content"]/div[1]/span[2]/text()')
        loader.add_xpath('title', '//div[@id="main-content"]/div[3]/span[2]/text()')
        loader.add_value('publishedTime', publishedDatetime)
        loader.add_xpath('content', '//div[@id="main-content"]')
        loader.add_value('canonicalUrl', response.url)
        # extract and transform comments
        pushs = response.xpath('//div[@id="main-content"]').css('div.push')
        comments = [self.extract_comment(push, publishedDatetime) for push in pushs]
        comments = [c for c in comments if c is not None]
        loader.add_value('comments', comments)
        item = loader.load_item()
        return item

    def extract_comment(self, push, pdate):
        commentId = push.css('span.push-userid::text').get()
        commentContent = push.css('span.push-content::text').get()[2:]
        try:
            commentTime = push.css('span.push-ipdatetime::text').get().strip()
            commentTime = dt.strptime(commentTime, '%m/%d %H:%M')
            # Because the year in not indicated within the comment.
            # So need to compare with date of the article to know the year.
            if commentTime.month < pdate.month:
                commentTime = commentTime.replace(year=(pdate.year + 1))
            else:
                commentTime = commentTime.replace(year=pdate.year)
            commentTime = int(commentTime.timestamp() * 1000)
        except (TypeError, ValueError):
            commentTime = None
        comment = {
            "commentId": commentId,
            "commentContent": commentContent,
            "commentTime": commentTime
        }
        return comment if None not in comment.values() else None
