# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import sys

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
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
        Rule(LxmlLinkExtractor(allow_domains=allowed_domains), callback='parse_item'),
    )

    def __init__(self, category=None, *args, **kwargs):
        super(GdriveSpider, self).__init__(*args, **kwargs)
        self.max_requests = 200
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


    # Callback for response from followed links
    def parse_item(self, response):
        if self.max_requests > 0 and self.counter == self.max_requests:
            raise CloseSpider('%d requests parsed' % self.counter)
        self.counter += 1

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

        item['title'] = title
        item['request_url'] = response.request.url
        item['location'] = response.url
        item['main_classes'] = main_classes
        item['contents'] = contents
        item['content_classes'] = content_classes

        # Files we want the FilesPipeline to download
        # For 'html' types with 'contents' the InlineHtml
        if file_type == 'pdf':
            if not title.lower().endswith('.pdf'):
                title += '.pdf'
            item['file_titles'] = [ title ]
            item['file_urls']   = [ response.url ]

        # Images we want the ImagesPipeline to download
        if file_type == 'html':
            # Need to build a list of img "alt" and "title"
            img_links = [l for l in self.img_link_extractor.extract_links(response)]
            if img_links:
                item['image_titles'] = [ ]
                item['image_urls'] = [ ]
                for link in self.process_img_links(img_links):
                    item['image_titles'].append(link.text)
                    item['image_urls'].append(link.url)
    
        yield item
