# job_spider.py
import scrapy
from items import JobItem
from pymongo import MongoClient
from config import Config

class JobSpider(scrapy.Spider):
    name = "job_spider"

    def __init__(self, *args, **kwargs):
        super(JobSpider, self).__init__(*args, **kwargs)
        self.start_urls = self.load_start_urls()

    def load_start_urls(self):
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.DATABASE_NAME]
        collection = db[Config.URLS_COLLECTION]
        urls = list(collection.find({}, {'_id': 0, 'url': 1}))
        client.close()
        return [url['url'] for url in urls]

    def parse(self, response):
        for job in response.xpath('//div[@class="job-description-wrapper"]'):
            item = JobItem(
                job_title=job.xpath('.//h5/a/text()').get(),
                job_detail_url=job.xpath('.//h5/a/@href').get(),
                job_listed=job.xpath('.//p[contains(@class, "job-recruiter")]/text()').get(),
                company_name=job.xpath('.//p[@class="job-recruiter"]/a[@class="company-name"]/text()').get(),
                company_link=job.xpath('.//p[@class="job-recruiter"]/a[@class="company-name"]/@href').get(),
                company_location=job.xpath('.//p[contains(@class, "location")]/text()').get()
            )
            
            # Set to None if any field is missing
            for field in item.fields:
                if item.get(field) is None:
                    item[field] = None
            
            yield item
