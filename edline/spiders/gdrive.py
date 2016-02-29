# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import sys
from six.moves.urllib.parse import urlparse, urljoin

import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.link import Link
from scrapy.linkextractors.lxmlhtml import LxmlParserLinkExtractor, LxmlLinkExtractor
from scrapy.spiders.crawl import CrawlSpider, Rule
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import unique as unique_list, str_to_unicode

from edline.items import PageItem

class ImgTitleLinkExtractor(LxmlParserLinkExtractor):
    def __init__(self, tag, attr, process=None, unique=False):
        super(ImgTitleLinkExtractor, self).__init__(tag, attr, process, unique)

    def _get_img_title(self, el):
        title = el.attrib.get('title', el.attrib.get('alt', u''))
        return title

    # Overriden to get text from the alt or title attribute
    def _extract_links(self, selector, response_url, response_encoding, base_url):
        links = []
        # hacky way to get the underlying lxml parsed document
        for el, attr, attr_val in self._iter_links(selector._root):
            # pseudo lxml.html.HtmlElement.make_links_absolute(base_url)
            try:
                attr_val = urljoin(base_url, attr_val)
            except ValueError:
                continue # skipping bogus links
            else:
                url = self.process_attr(attr_val)
                if url is None:
                    continue
            if isinstance(url, unicode):
                url = url.encode(response_encoding)
            # to fix relative links after process_value
            url = urljoin(response_url, url)
            link = Link(url, self._get_img_title(el),
                nofollow=True if el.get('rel') == 'nofollow' else False)
            links.append(link)

        return unique_list(links, key=lambda link: link.url) \
                if self.unique else links

class ImgLinkExtractor(LxmlLinkExtractor):

    # Overridden to use ImgTitleLinkExtractor to parse titles
    def __init__(self, allow=(), deny=(), allow_domains=(), deny_domains=(), restrict_xpaths=(),
                 tags=('a', 'area'), attrs=('href',), canonicalize=True,
                 unique=True, process_value=None, deny_extensions=None, restrict_css=()):
        tags, attrs = set(arg_to_iter(tags)), set(arg_to_iter(attrs))
        tag_func = lambda x: x in tags
        attr_func = lambda x: x in attrs
        lx = ImgTitleLinkExtractor(tag=tag_func, attr=attr_func,
            unique=unique, process=process_value)

        super(LxmlLinkExtractor, self).__init__(lx, allow=allow, deny=deny,
            allow_domains=allow_domains, deny_domains=deny_domains,
            restrict_xpaths=restrict_xpaths, restrict_css=restrict_css,
            canonicalize=canonicalize, deny_extensions=deny_extensions)


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
        'http://www.kentfieldschools.org/pages/Kentfield_School_District/Support_Kentfield_Schools',

        # 'http://www.kentfieldschools.org',
    )
    rules = (
        Rule(LxmlLinkExtractor(allow_domains=allowed_domains), callback='parse_item'),
    )

    types = (
        (r'text/html', 'html'),
        (r'application/pdf', 'pdf'),
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

    def _get_type(self, response):
        content_type = response.headers.get('content-type', None)
        file_type = None
        for pat, ext in self.types:
            if re.search(pat, content_type):
                return (content_type, ext)
        print('unknown content_type %s' % content_type)
        return (content_type, None)

    # Callback for response from followed links
    def parse_item(self, response):
        if self.max_requests > 0 and self.counter == self.max_requests:
            raise CloseSpider('%d requests parsed' % self.counter)
        self.counter += 1

        content_type, file_type = self._get_type(response)
        title = None
        main_classes = [ ]
        contents = None
        content_classes = [ ]

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
                        content_type += '; edline=inline'

            # List the class names
            for div in  response.xpath('//div[@role="main"]'):
                xclass = div.xpath('@class').extract_first()
                if xclass:
                    main_class_name = re.split(r'\s+', xclass)[0]
                    main_classes.append(main_class_name)

        if title is None:
            title = response.request.meta.get('link_text', 'Untitled')

        item = PageItem()
        item['title'] = title
        item['request_url'] = response.request.url
        item['location'] = response.url
        item['content_type'] = content_type
        item['main_classes'] = main_classes
        item['contents'] = contents
        item['content_classes'] = content_classes

        # Files we want the FilesPipeline to download
        if file_type == 'pdf':
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
