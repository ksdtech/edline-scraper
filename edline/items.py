# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import re

import scrapy

# MCE Document div.edlDocViewBoxContents
# Doc-in-a-box 
class PageItem(scrapy.Item):
    types = (
        (r'text/html', 'html'),
        (r'application/pdf', 'pdf'),
    )

    title        = scrapy.Field()
    request_url  = scrapy.Field()
    location     = scrapy.Field()
    content_type = scrapy.Field()
    file_type    = scrapy.Field()
    file_urls    = scrapy.Field()
    file_metas   = scrapy.Field()
    files        = scrapy.Field()  # downloaded files
    image_urls   = scrapy.Field()
    image_metas  = scrapy.Field()
    images       = scrapy.Field()
    main_classes = scrapy.Field()
    contents     = scrapy.Field()
    content_classes = scrapy.Field()

    @classmethod
    def get_file_type(cls, content_type):
        file_type = None
        for pat, ext in cls.types:
            if re.search(pat, content_type):
                return ext
        print('unknown content_type %s' % content_type)
        return None

    def set_file_type(self):
        self['file_type'] = self.__class__.get_file_type(self['content_type'])
        return self['file_type']

