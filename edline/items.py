# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import re

import scrapy

KNOWN_TYPES = {
    'text/html': 'html',
    'application/pdf': 'pdf',
    'image/jpeg': 'jpg',  # mimetypes.guess_extension returns '.jpe'
}

def get_file_type(content_type):
    mime_type = re.sub(r'\s*[;].*$', '', content_type)
    ext = KNOWN_TYPES.get(mime_type)
    if not ext:
        ext = mimetypes.guess_extension(mime_type)
        if ext:
            ext = ext[1:]
        print('content_type %s -> %r' % (content_type, ext))
    return ext

# MCE Document div.edlDocViewBoxContents
# Doc-in-a-box 
class PageItem(scrapy.Item):
    title        = scrapy.Field()
    request_url  = scrapy.Field()
    location     = scrapy.Field()
    content_type = scrapy.Field()
    file_type    = scrapy.Field()
    file_urls    = scrapy.Field()
    file_metas   = scrapy.Field()
    files        = scrapy.Field()
    image_urls   = scrapy.Field()
    image_metas  = scrapy.Field()
    images       = scrapy.Field()
    inline_urls  = scrapy.Field()
    inline_metas = scrapy.Field()
    inlines      = scrapy.Field() 
    main_classes = scrapy.Field()
    contents     = scrapy.Field()
    content_classes = scrapy.Field()

    def set_file_type(self):
        self['file_type'] = get_file_type(self['content_type'])
        return self['file_type']

