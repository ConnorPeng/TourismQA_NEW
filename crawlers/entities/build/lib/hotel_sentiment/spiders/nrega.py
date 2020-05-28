import scrapy
from hotel_sentiment.items import HotelSentimentItem

#TODO use loaders
class NREGAScraper(scrapy.Spider):
    name = "nrega"
    start_urls = [
		"http://nregasp2.nic.in/netnrega/state_html/pmsr.aspx?lflag=local&state_code=05&state_name=BIHAR&fin_year=2016-2017&page=S&Digest=UUQwSH3Ebnl2wwvs85LBTg"
#		"https://www.tripadvisor.in/Hotels-g297684-Lucknow_Lucknow_District_Uttar_Pradesh-Hotels.html",
#		"https://www.tripadvisor.com/Hotels-g295424-Dubai_Emirate_of_Dubai-Hotels.html",
#		"https://www.tripadvisor.com/Hotels-g60763-New_York_City_New_York-Hotels.html"
		#"www.tripadvisor.in/Shimla/TopHotels",
		#"www.tripadvisor.in/London/TopHotels",
		#"www.tripadvisor.in/Innsbruck/TopHotels",
		#"www.tripadvisor.in/Vienna/TopHotels",
		#"www.tripadvisor.in/Madrid/TopHotels",
		#"www.tripadvisor.in/Chicago/TopHotels",
		#www.tripadvisor.in/Bukhara/TopHotels",		
    ]

    def parse(self, response):
        for href in response.xpath('//tr//td//a/@href'):
            url = response.urljoin(href.extract())
            print "URL 1 " +  url
            yield scrapy.Request(url, callback=self.parse_page2)

        #next_page = response.xpath('//div[@class="unified pagination standard_pagination"]/child::*[2][self::a]/@href')
        #if next_page:
            #url = response.urljoin(next_page[0].extract())
            #yield scrapy.Request(url, self.parse)
			
    def parse_page2(self, response):
        for href in response.xpath('//tr//td//a/@href'):
            url = response.urljoin(href.extract())
            print "URL 2" + url
            yield scrapy.Request(url, callback=self.parse_page3)

        #next_page = response.xpath('//div[@class="unified pagination standard_pagination"]/child::*[2][self::a]/@href')
        #if next_page:
         #   url = response.urljoin(next_page[0].extract())
          #  yield scrapy.Request(url, self.parse)

    def parse_page3(self, response):
        print "TABLE: "+response.xpath('//table/')
        for table in response.xpath('//table'):
            #url = response.urljoin(href.extract())
            print table
            #yield scrapy.Request(url, callback=self.parse_review)

        #next_page = response.xpath('//div[@class="unified pagination "]/child::*[2][self::a]/@href')
        #if next_page:
         #   url = response.urljoin(next_page[0].extract())
          #  yield scrapy.Request(url, self.parse_hotel)


    #to get the full review content I open its page, because I don't get the full content on the main page
    #there's probably a better way to do it, requires investigation
    def parse_review(self, response):
        item = HotelSentimentItem()
        item['name']= response.xpath('//span[@class="altHeadInline"]/a/text()').extract()
        item['address']= response.xpath('(//span[@class="street-address"])[1]/text()').extract() + response.xpath('(//span[@class="extended-address"])[1]/text()').extract() + response.xpath('(//span[@class="locality"])[1]/text()').extract()# + response.xpath('//span[@class="extended-address"]/text()').extract() + response.xpath('//span[@class="locality"]/text()').extract()
        item['title'] = response.xpath('//div[@class="quote"]/text()').extract()[0][1:-1] #strip the quotes (first and last char)
        item['content'] = response.xpath('//div[@class="entry"]/p/text()').extract()[0]
        item['amenity'] =response.xpath('//span[@class="amenity"]/text()').extract()
        item['hotel_class']= response.xpath('//div//span[@class="hClass"]/parent::*/text()').extract()
        item['num_rooms']=response.xpath('//span[@class="tabs_num_rooms"]/text()').extract()
        item['review_rating']=  response.xpath('//span[@property="reviewRating"]/span/@content').extract()
        item['review_date']=  response.xpath('//span[@property="datePublished"]/@content').extract()
		
        
        #item['stars'] = response.xpath('//span[@class="rate sprite-rating_s rating_s"]/img/@alt').extract()[0]
        return item
