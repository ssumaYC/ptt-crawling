# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from ptt_spider.settings import REDIS_HOST, MONGO_HOST, PTT_DB
from pymongo import MongoClient
from redis import Redis
from scrapy.exceptions import DropItem
from datetime import datetime as dt


class PttSpiderPipeline(object):

    def open_spider(self, spider):
        # init connection with MongoDB and Redis
        self.client = MongoClient(MONGO_HOST)
        self.db = self.client[PTT_DB]
        self.r = Redis(host=REDIS_HOST)

    def close_spider(self, spider):
        # remove job_id from redis, since the job is done
        self.r.delete(spider.job_id)
        # close connection while closing spider
        self.client.close()
        self.r.close()

    def process_item(self, item, spider):
        # check needed fields exists otherwise drop item
        needed_fields = {
            'authorId', "authorName", "title",
            "publishedTime", "content", "canonicalUrl"}
        missing_fields = needed_fields - set(item.keys())
        if missing_fields != set():
            raise DropItem(missing_fields)
        # init collection
        article_col = self.db['article']
        comment_col = self.db['comment']
        # use authorId and publishedTime as unique ID for document
        author_and_time = {
            "authorId": item.pop('authorId'),
            "publishedTime": item.pop('publishedTime')
        }
        # extract comments from article and update unique ID for comments
        comments = item.pop('comments', None)
        article = dict(item)
        now = dt.now()
        article['updateTime'] = now
        # update article and comments to MongoDB
        article_col.update_one(
            author_and_time,
            {
                "$set": article,
                "$setOnInsert": {'createdTime': now}
            },
            upsert=True)
        if comments is not None:
            comments = [{**c, **author_and_time} for c in comments]
            comment_col.remove(author_and_time)
            comment_col.insert_many(comments)
        # record url in redis
        self.r.sadd(spider.job_id, article['canonicalUrl'])
        return item
