# -*- coding: utf-8 -*-
from __future__ import print_function

import codecs
import hashlib
import os

from six.moves.urllib.parse import urlparse, urljoin
from six.moves.urllib.request import pathname2url
from twisted.internet.defer import DeferredList

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.files import FSFilesStore, S3FilesStore
from scrapy.utils.misc import md5sum
from scrapy.exceptions import DropItem, NotConfigured

# Much code taken from scrapy MediaPipeline and FilesPipeline
class InlineHtmlPipeline(object):

  LOG_FAILED_RESULTS = True

  STORE_SCHEMES = {
    '': FSFilesStore,
    'file': FSFilesStore,
    's3': S3FilesStore,
  }

  DEFAULT_FILES_URLS_FIELD = 'file_urls'
  DEFAULT_FILES_RESULT_FIELD = 'files'

  class SpiderInfo(object):
    def __init__(self, spider):
      self.spider = spider

  def __init__(self, store_uri):
    if not store_uri:
      raise NotConfigured
    self.store = self._get_store(store_uri)
    try:
      os.makedirs(os.path.join(self.store.basedir, 'full'))
    except:
      pass
    self.counter = 0

  @classmethod
  def from_settings(cls, settings):
    cls.FILES_URLS_FIELD = settings.get('FILES_URLS_FIELD', cls.DEFAULT_FILES_URLS_FIELD)
    cls.FILES_RESULT_FIELD = settings.get('FILES_RESULT_FIELD', cls.DEFAULT_FILES_RESULT_FIELD)
    store_uri = settings['FILES_STORE']
    return cls(store_uri)

  @classmethod
  def from_crawler(cls, crawler):
    # try:
    pipe = cls.from_settings(crawler.settings)
    # except AttributeError:
    # pipe = cls()
    pipe.crawler = crawler
    return pipe

  def open_spider(self, spider):
    self.spiderinfo = self.SpiderInfo(spider)

  def _get_store(self, uri):
    if os.path.isabs(uri):  # to support win32 paths like: C:\\some\dir
      scheme = 'file'
    else:
      scheme = urlparse(uri).scheme
    store_cls = self.STORE_SCHEMES[scheme]
    return store_cls(uri)

  def write_item(self, item):
    title = item.get('title', 'Untitled')
    header = """<html lang="en">
<head>
<meta charset="utf-8" />
<title>%s</title>
</head>
<body>
""" % title

    closer = """
</body>
</html>
"""
    
    url = item['location']
    media_guid = hashlib.sha1(url).hexdigest()
    media_ext = '.html' 
    path = 'full/%s%s' % (media_guid, media_ext)
    absolute_path = os.path.join(self.store.basedir, path)
    with codecs.open(absolute_path, 'wb', 'utf-8') as f:
      f.write(header)
      f.write('<h2>%s</h2>\n' % title)
      f.write(item['contents'])
      f.write(closer)

    checksum = None
    with open(absolute_path, 'rb') as f:
      checksum = md5sum(f)

    # Compatible with Twisted Deferred results
    results = [
      (True, {'url': url,
        'path': path,
        'checksum': checksum }
      )
    ]

    item[self.FILES_URLS_FIELD] = [ urljoin('file://', pathname2url(absolute_path)) ]
    item['file_titles'] = [ title ]
    item = self.item_completed(results, item, self.spiderinfo)
    return item

  def item_completed(self, results, item, info):
    if isinstance(item, dict) or self.FILES_RESULT_FIELD in item.fields:
      item[self.FILES_RESULT_FIELD] = [x for ok, x in results if ok]
 
    if self.LOG_FAILED_RESULTS:
      for ok, value in results:
        if not ok:
          logger.error(
            '%(class)s found errors processing %(item)s',
            {'class': self.__class__.__name__, 'item': item},
            exc_info=failure_to_exc_info(value),
            extra={'spider': info.spider}
          )
    return item

  def process_item(self, item, spider):
    self.counter += 1

    if item['contents'] is not None:
      item = self.write_item(item)
    return item
