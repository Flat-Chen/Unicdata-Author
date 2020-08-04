# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import pymongo
import logging
from pybloom_live import ScalableBloomFilter
from hashlib import md5
import pathlib
import os
import time
from scrapy.exceptions import DropItem
import requests
import json


class AutohomePipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        # mongo
        self.connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = self.connection[settings['MONGODB_DB']]
        website = settings["WEBSITE"]
        # local_time = time.strftime('%Y-%m-%d', time.localtime())
        # if website in ["pcauto_price", "yiche_price", "autohome_price"]:
        #     self.collection = db[settings['MONGODB_COLLECTION'] + '_' + str(local_time)]
        # else:
        self.collection = db[settings['MONGODB_COLLECTION']]
        # bloom file
        self.CrawlCar_Num = 1000000
        filename = str(pathlib.Path.cwd()) + '/blm/' + settings['MONGODB_DB'] + '/' + settings[
            'MONGODB_COLLECTION'] + '.blm'
        dirname = str(pathlib.Path.cwd()) + '/blm/' + settings['MONGODB_DB']
        self.df = ScalableBloomFilter(initial_capacity=self.CrawlCar_Num, error_rate=0.01)
        if os.path.exists(dirname):
            if os.path.exists(filename):
                self.fa = open(filename, "a")
            else:
                pathlib.Path(filename).touch()
                self.fa = open(filename, "a")
        else:
            os.makedirs(dirname)
            pathlib.Path(filename).touch()
            self.fa = open(filename, "a")

        with open(filename, "r") as fr:
            lines = fr.readlines()
            for line in lines:
                line = line.strip('\n')
                self.df.add(line)
        self.counts = 0

    def process_item(self, item, spider):
        if spider.name in ["111"]:
            valid = True
            i = md5(item['status'].encode("utf8")).hexdigest()
            returndf = self.df.add(i)
            if returndf:
                valid = False
                raise DropItem("Drop data {0}!".format(item["status"]))
            else:
                self.fa.writelines(i + '\n')
                self.collection.insert(dict(item))
                logging.log(msg="Car added to MongoDB database!", level=logging.INFO)
                self.counts += 1
                logging.log(msg="scrapy                    " + str(self.counts) + "                  items",
                            level=logging.INFO)
                # return item
        elif spider.name in ["autohome_rank", "yiche_price", "pcauto_price", "58car_price"]:
            self.collection.insert(dict(item))
            logging.log(msg="Car added to MongoDB database!", level=logging.INFO)
            self.counts += 1
            logging.log(msg="scrapy                    " + str(self.counts) + "                  items",
                        level=logging.INFO)
        else:
            self.collection.insert(dict(item))
            logging.log(msg="Car added to MongoDB database!", level=logging.INFO)
            self.counts += 1
            logging.log(msg="scrapy                    " + str(self.counts) + "                  items",
                        level=logging.INFO)

    def close_spider(self, spider):
        self.connection.close()

        # self.fa.close()

    def dingmessage(self):
        # 请求的URL，WebHook地址
        webhook = "https://oapi.dingtalk.com/robot/send?access_token=633758ccd22b7db4d2e9655488af7d3f5d5e0b2a32c701c80fc3cd57981e73a9"
        # 构建请求头部
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        # 构建请求数据
        tex = "-车秀网爬虫结束-"
        message = {

            "msgtype": "text",
            "text": {
                "content": tex
            },
            "at": {

                "isAtAll": False
            }

        }
        # 对请求的数据进行json封装
        message_json = json.dumps(message)
        # 发送请求
        info = requests.post(url=webhook, data=message_json, headers=header)
        # 打印返回的结果
        print(info.text)
