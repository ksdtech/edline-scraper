# -*- coding: utf-8 -*-
from __future__ import print_function

from six.moves.urllib.parse import urlparse, urljoin

from scrapy.link import Link
from scrapy.linkextractors.lxmlhtml import LxmlParserLinkExtractor, LxmlLinkExtractor
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import unique as unique_list

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
