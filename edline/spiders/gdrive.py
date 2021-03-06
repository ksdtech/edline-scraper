# -*- coding: utf-8 -*-
from __future__ import print_function

import mimetypes
import os
import re
import sys

from six.moves.urllib.parse import urlparse, urlunparse

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.http import Request, HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders.crawl import CrawlSpider, Rule

from edline.items import PageItem
from edline.linkextractors import ImgLinkExtractor

class GdriveSpider(CrawlSpider):
    name = "gdrive"
    allowed_domains = [
        'www.kentfieldschools.org',
        'www.edlinesites.net'
    ]
    start_urls = (
        # An example with inline TMCE content
        # 'http://www.kentfieldschools.org/pages/Kentfield_School_District/Administration/Technology/Technology_Overview',

        # An example with PDF content
        # 'http://www.kentfieldschools.org/pages/Kentfield_School_District/Get_Involved/KSF/2015-2016_kik',

        # Page with an img link on it
        # 'http://www.kentfieldschools.org/pages/Kentfield_School_District/Support_Kentfield_Schools',

        # 'http://www.edlinesites.net/pages/Bacich_Elementary_School',
        # 'http://www.edlinesites.net/pages/Kent_Middle_School',
        'http://www.kentfieldschools.org',
    )
    rules = (
        Rule(LinkExtractor(allow_domains=allowed_domains), callback='parse_item', follow=True),
    )

    def __init__(self, *args, **kwargs):
        super(GdriveSpider, self).__init__(*args, **kwargs)
        if 'max_requests' in kwargs:
            self.max_requests = int(kwargs['max_requests'])
        else:
            self.max_requests = 0 # unlimiited
        print('Starting GDriveSpider with maximum %d requests' % self.max_requests)
        self.counter = 0
        self.img_link_extractor = ImgLinkExtractor(tags=('img', 'audio', 'video'), attrs=('src',),
            allow_domains=self.allowed_domains, deny_extensions=[])

    # Used to filter out links
    def process_img_links(self, links):
        content_links = [ ]
        for link in links:
            if re.search(r'\/images\/site_designer\/', link.url):
                # print('discarding designer image %s' % link.url)
                pass
            else: 
                content_links.append(link) 
        return content_links

    # TODO: Override _requests_to_follow to add referer meta
    # r.meta.update(rule=n, link_text=link.text, referer=response.url)

    # Callback for response from followed links
    def parse_item(self, response):
        if self.max_requests > 0 and self.counter >= self.max_requests:
            raise CloseSpider('%d requests parsed' % self.counter)
        self.counter += 1

        request_url = response.request.url
        if self.counter % 50 == 0:
            print('Request # %d: %s' % (self.counter, request_url))

        title = None
        main_classes = [ ]
        contents = None
        content_classes = [ ]

        item = PageItem()
        item['content_type'] = response.headers.get('content-type', None)
        file_type = item.set_file_type()
        if file_type == 'html':
            xtitle = response.xpath('//head/meta[@property="og:title"]/@content').extract_first()
            if not xtitle:
                xtitle = response.xpath('//head/title/text()').extract_first()
            if xtitle:
                title = xtitle.split(':', 1)[-1].strip()

            # Find inline content
            for content_div in response.xpath('//div[@role="main"]//div[@class="edlDocViewBoxContents"]/div'):
                xclass = content_div.xpath('@class').extract_first()
                if xclass:
                    content_class_names = re.split(r'\s+', xclass)
                    content_classes.extend(content_class_names)
                    if contents is None and 'edlInlineTMCE' in content_class_names:
                        contents = '\n'.join(content_div.xpath('child::node()').extract()).strip()
                        item['content_type'] = item['content_type'] + '; edline=inline'

            # List the class names
            for div in  response.xpath('//div[@role="main"]'):
                xclass = div.xpath('@class').extract_first()
                if xclass:
                    main_class_name = re.split(r'\s+', xclass)[0]
                    main_classes.append(main_class_name)

        if title is None:
            title = response.request.meta.get('link_text', 'Untitled')
        # Remove trailing dots
        title = re.sub(r'[.\s]+$', '', title)

        item['title'] = title
        item['request_url'] = request_url
        item['location'] = response.url
        item['main_classes'] = main_classes
        item['contents'] = contents
        item['content_classes'] = content_classes

        # Files we want the FilesPipeline to download
        if file_type == 'pdf':
            item['location'] = response.request.headers.get('Referer', request_url)
            if not title.lower().endswith('.pdf'):
                title += '.pdf'
            item['file_urls']  = [ response.url ]
            item['file_metas'] = [ { 'link_url': item['request_url'], 'location': item['location'], 
                'title': title, 'content_type': 'application/pdf' } ]

        # Images we want the ImagesPipeline to download
        if file_type == 'html':
            # Need to build a list of img "alt" and "title"
            img_links = [l for l in self.img_link_extractor.extract_links(response)]
            if img_links:
                item['image_urls']  = [ ]
                item['image_metas'] = [ ]
                for link in self.process_img_links(img_links):
                    u = urlparse(link.url)
                    title = link.text
                    content_type = mimetypes.guess_type(u.path, strict=False)                    
                    fpath, ext = os.path.splitext(u.path)
                    if title is None or title.strip() == '':
                        title = os.path.basename(fpath)
                    title += ext.lower()
                    item['image_urls'].append(link.url)
                    item['image_metas'].append( { 'link_url': link.url, 'location': item['location'], 
                        'title': title, 'content_type': content_type } )
    
        # If the item is an HTML response and has 'contents'
        # The InlineHtmlPipeline will create a file and create the 'inlines'
        yield item
