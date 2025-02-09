import os
import re
import json
import scrapy
from urllib.parse import urlencode, parse_qs, urlunparse, urlparse
from nested_lookup import nested_lookup
from inline_requests import inline_requests

from . import Processor

class Parser:
    def __init__(self):
        pass

    def cleanURL(self, url):
        parsed_url = list(urlparse(url))
        qs = parse_qs(parsed_url[4], keep_blank_values = True)
        for param in ["label", "sid"]:
            if(param in qs):
                del qs[param]
        parsed_url[4] = urlencode(qs, doseq = True)
        url = urlunparse(parsed_url)
        return url

    def getBaseReviewPageUrl(self, hotel_url):
        cc1 = hotel_url.split("/")[-2]
        pagename = hotel_url.split("/")[-1].split(".")[0]
        params = {"cc1": cc1, "pagename": pagename, "rows": 10, "offset": 0}
        base_review_page_url = "https://www.booking.com/reviewlist.en-gb.html?" + urlencode(params)
        return base_review_page_url

    def getReviewItem(self, selector, url):
        item = {}

        item["title"] = selector.xpath('//h3[contains(@class,"c-review-block__title")]/text()').get() or ""
        item["description"] = " ".join(selector.xpath('//span[@class="c-review__body"]//text()').extract())
        item["rating"] = selector.xpath('//div[@class="bui-review-score__badge"]/text()').get() or ""
        
        # Fix date parsing with error handling
        date_text = selector.xpath('//span[@class="c-review-block__date"]//text()').get() or ""
        try:
            item["date"] = date_text.split(": ")[1] if ": " in date_text else date_text
        except (IndexError, AttributeError):
            item["date"] = date_text
            
        item["url"] = url

        return item

    def getEntityItem(self, response):
        item = {}

        try:
            data = json.loads(response.xpath('//script[@type="application/ld+json"]//text()').extract_first() or '{}')
            item["name"] = data.get("name", "")
            item["address"] = data.get("address", {}).get("streetAddress", "")
            item["rating"] = data.get("aggregateRating", {}).get("ratingValue", 0)/2 if data.get("aggregateRating") else 0
        except (json.JSONDecodeError, AttributeError):
            item["name"] = ""
            item["address"] = ""
            item["rating"] = 0

        try:
            coords_match = re.search(r'defaultCoordinates:\s*(\[\s*[\'"][-\d.]+[\'"]\s*,\s*[\'"][-\d.]+[\'"]\s*\])', response.text)
            if coords_match:
                coords = json.loads(coords_match.group(1).replace("'", '"'))
                item["latitude"] = coords[0]
                item["longitude"] = coords[1]
            else:
                item["latitude"] = ""
                item["longitude"] = ""
        except (json.JSONDecodeError, IndexError):
            item["latitude"] = ""
            item["longitude"] = ""

        item["properties"] = response.xpath('//div[contains(@class, "important_facility")]/text()').extract()
        item["description"] = " ".join(response.xpath('//div[@id="property_description_content"]//p//text()').extract())
        item["url"] = response.url

        return item

class Crawler(scrapy.Spider):
    name = 'hotels_crawler'  # Add spider name
    
    def __init__(self, items):
        self.items = items
        self.parser = Parser()
        self.processor = Processor.Processor()

    def start_requests(self):
        for item in self.items:
            yield scrapy.Request(item["url"], meta = {"id": item["id"]})

    def getReviewItems(self, response):
        url = self.parser.cleanURL(response.url)
        review_selectors = response.xpath('//ul[@class="review_list"]/li')
        for review_selector in review_selectors:
            yield self.parser.getReviewItem(scrapy.Selector(text = review_selector.extract()), url)

    @inline_requests
    def parse(self, response):
        item = self.parser.getEntityItem(response)
        item["id"] = response.meta["id"]

        base_review_page_url = self.parser.getBaseReviewPageUrl(response.url)
        response = yield scrapy.Request(base_review_page_url, headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36", "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"})

        reviews = []
        while(1):
            for review in self.getReviewItems(response):
                reviews.append(review)

            next_page_href = response.xpath('//a[@class="pagenext"]/@href').get()
            if(not next_page_href):
                break

            url = response.urljoin(next_page_href)
            response = yield scrapy.Request(url, headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36", "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"})

        item["reviews"] = reviews
        yield self.processor.processEntityItem(item)
