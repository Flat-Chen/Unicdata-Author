#-*- coding: UTF-8 -*-
import scrapy
from ganji.items import GanjiItem
import time
import logging
from hashlib import md5
from SpiderInit import spider_original_Init
from SpiderInit import spider_new_Init
from SpiderInit import spider_update_Init
from SpiderInit import dfcheck
from SpiderInit import dffile
from Car_spider_update import update
import json


website ='hb'
spidername_new = 'hb_new'
spidername_update = 'hb_update'

#main
class CarSpider(scrapy.Spider):
    #basesetting
    name = website
    allowed_domains = ["harbin-ershouche.com"]
    start_urls = [
        "http://www.harbin-ershouche.com/harbin/a0b0c0d0e0f0g0h0l3i0j0k0o0m1n.html"
    ]


    def __init__(self, **kwargs):
        # args
        super(CarSpider, self).__init__(**kwargs)
        #setting
        self.tag='original'
        self.counts=0
        self.carnum=300000
        self.dbname = 'usedcar'
        # spider setting

        spider_original_Init(
            dbname=self.dbname,
            website=website,
            carnum=self.carnum)
        self.df='none'
        self.fa='none'

    #get car list
    def parse(self, response):
        #car_item
        for href in response.xpath('//div[@class="con_left"]//div/a[@target="_blank"]'):
            urlbase = href.xpath("@href").extract_first()
            datasave1 = href.extract()
            url = response.urljoin(urlbase)
            if not (dfcheck(self.df, url, self.tag)):
                try:
                    yield scrapy.Request(url,meta={"datasave1":datasave1},callback= self.parse_car)
                except:
                    pass

        # next page
        next_page = response.xpath(u'//div[@id="page"]/a[contains(text(),"下一页")]/@href')
        if next_page:
            url = response.urljoin(next_page.extract_first())
            try:
                yield scrapy.Request(url, self.parse)
            except:
                pass

    # get car infor
    def parse_car(self, response):
        # requests count
        if self.tag == 'update':
            addcounts = self.request_next()
            if addcounts:
                self.size = min(self.size, self.carnum - self.reqcounts)
                for i in range(self.reqcounts, self.reqcounts + self.size):
                    url = self.urllist[i]
                    if url:
                        yield scrapy.Request(url, callback=self.parse_car, errback=self.error_parse)

        if response.status == 200:
            # count
            self.counts += 1
            logging.log(msg="download              " + str(self.counts) + "                  items", level=logging.INFO)
            # dffile
            dffile(self.fa, response.url, self.tag)
            # datasave baseinfo
            if response.meta.has_key('datasave1'):
                datasave1 = response.meta['datasave1']
            else:
                datasave1 = 'zero'
            # key and status (sold or sale, price,time)
            #未找到状态
            # status = response.xpath('//div[@class="right-sold"]')
            # if status:
            #     status = "sold"
            #     price = response.xpath(u'//p[contains(text(),'价格')]/b/text()')
            # else:
            status = "sale"
            price = response.xpath('//div[@class="carIn"]/p/em/text()').extract_first()
            price = str(price) if price else "zero"
            datetime = "zero"
            # item loader
            item = GanjiItem()
            item['url'] = response.url
            item['grabtime'] = time.strftime('%Y-%m-%d %X', time.localtime())
            item['website'] = website
            item['status'] = response.url + "-" + str(price) + "-" + str(status) + "-" + datetime
            item['pagetime'] = datetime
            item['datasave'] = [datasave1, response.xpath('//html').extract_first()]
            # with open("C:\Users\Admin\Desktop\hb\hb.text", 'a') as f:
            #     print('********************************************')
            #     json.dump({"url":response.url,
            #                'grabtime':time.strftime('%Y-%m-%d %X', time.localtime()),
            #                'website':website,
            #                'status':response.url + "-" + str(price) + "-" + str(status) + "-" + datetime,
            #                'pagetime':datetime
            #                },
            #               f)
            #     f.write("\n")
            yield item

#new
class CarSpider_new(CarSpider):

    #basesetting
    name = spidername_new

    def __init__(self, **kwargs):
        # args
        super(CarSpider_new, self).__init__(**kwargs)
        #tag
        self.tag='new'
        # spider setting
        self.df =spider_new_Init(
                spidername=spidername_new,
                dbname=self.dbname,
                website=website,
                carnum=self.carnum)
        filename = 'blm/' + self.dbname + '/' + spidername_new + ".blm"
        self.fa = open(filename, "a")

#update
class CarSpider_update(CarSpider,update):

    #basesetting
    name = spidername_update

    def __init__(self, **kwargs):
        # load
        super(CarSpider_update, self).__init__(**kwargs)
        #settings
        self.urllist = spider_update_Init(
            dbname=self.dbname,
            website=website,
            carnum=self.carnum
        )
        self.carnum = len(self.urllist)
        self.tag='update'
        #do
        super(update, self).start_requests()