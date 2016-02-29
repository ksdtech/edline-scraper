# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

# MCE Document div.edlDocViewBoxContents
# Doc-in-a-box 
class PageItem(scrapy.Item):
    request_url  = scrapy.Field()
    content_type = scrapy.Field()
    location     = scrapy.Field()
    title        = scrapy.Field()
    image_titles = scrapy.Field()
    image_urls   = scrapy.Field()
    images       = scrapy.Field()
    file_titles  = scrapy.Field()
    file_urls    = scrapy.Field()
    files        = scrapy.Field()  # downloaded files
    main_classes = scrapy.Field()
    contents     = scrapy.Field()
    content_classes = scrapy.Field()
