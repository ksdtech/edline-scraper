import cgi
import codecs
import os
import re
import sys

from six.moves.urllib.parse import urljoin, urlparse, urlunparse

# Find patched bleach module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../bleach'))
from bleach import clean

from bs4 import BeautifulSoup

# mozilla/bleach and or html5lib tokenizer/sanitizer still have some bugs
# 1.  <html><head><style> doesn't seem to be stripped
# 2.  html entities are messed up. See https://github.com/mozilla/bleach/issues/143
# 3.  Find some way to remove "empty" elements, such as: <a></a>, <li></li>, <p></p> etc.
# 4.  Remove <span> tag if "class" attribute was filtered out

ENTITY_REPLACEMENTS = {
    '\xa0': ' '
}

def swap_entities(text):
    for k, v in ENTITY_REPLACEMENTS.items():
        text = re.sub(k, v, text)
    return text

def remove_empty_ps(text):
    text = re.sub(r'<p>\s*(\&nbsp\;)?\s*</p>', '', text)
    return text

def canonical_url(base_url, href):
    link_url = urljoin(base_url, href)
    u = urlparse(link_url)
    canonical_url = urlunparse((u.scheme, u.netloc, u.path, None, None, None)).lower()
    return canonical_url

def add_link_text(text, base_url, links):
    mod_count = 0
    soup = BeautifulSoup(text)
    for a in soup.findAll('a'):
        if 'href' in a:
            url = canonical_url(base_url, a['href'])
            if url in links:
                strong = soup.new_tag('strong')
                strong.string = '[ ' + links[url]['href'] + ' ]'
                a.insert_before(strong)
                mod_count += 1
    for img in soup.findAll('img'):
        if 'src' in img:
            url = canonical_url(base_url, img['src'])
            if url in links:
                strong = soup.new_tag('strong')
                strong.string = '[ ' + links[url]['href'] + ' ]'
                img.insert_before(strong)
                mod_count += 1
    if mod_count:
        return soup.prettify()
    return text

MY_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'address',
    'area',
    'article',
    'audio',
    'b',
    # 'bdi',
    # 'bdo',
    'br',
    'blockquote',
    'canvas',
    'caption',
    'cite',
    'code',
    'col',
    'colgroup',
    # 'data',
    'dfn',
    'dd',
    'del',
    'div',
    'dl',
    'dt'
    'em',
    'embed',
    'figcaption',
    'figure',
    'footer',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'header',
    'hgroup',
    'hr',
    'i',
    'img',
    'ins',
    'kbd',
    'li',
    'main',
    'mark',
    'map',
    'nav',
    'noscript',
    'object',
    'ol',
    'p',
    # 'param',
    'pre',
    'q',
    # 'rp',
    # 'rt',
    # 'rtc',
    # 'ruby',
    'samp',
    'script',
    'section',
    'small',
    # 'source',
    # 'span',
    'strong',
    'sub',
    'sup',
    'table',
    'tbody',
    'td',
    'tfoot',
    'th',
    'thead',
    'time',
    'tr',
    'track',
    'u',
    'ul',
    'var',
    'video',
    'wbr',
]

MY_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
    'img': ['src', 'alt', 'style', 'width', 'height'],
}

MY_ALLOWED_STYLES = [
    'width', 'height'
]

def sanitize(content, base_url, links):
    i = content.index('<body>') + 6
    j = content.index('</body>')
    body = clean(content[i:j],
        tags=MY_ALLOWED_TAGS, attributes=MY_ALLOWED_ATTRIBUTES,
        styles=MY_ALLOWED_STYLES, strip=True, strip_comments=True)
    body = swap_entities(body)
    body = remove_empty_ps(body)
    body = add_link_text(body, base_url, links)
    html = content[0:i] + body + content[j:]
    return html

def make_cleaned_path(file_from):
    dirname, basename = os.path.split(file_from)

    dirparent = os.path.dirname(dirname)
    dirname = os.path.join(dirparent, 'cleaned')
    try:
        os.makedirs(dirname)
    except:
        pass
    return os.path.join(dirname, basename)

def sanitize_html_file(file_in, file_out, base_url=None, links={}):
    with codecs.open(file_in, 'r', 'utf-8') as f_in:
        file_content = f_in.read()
        sanitized_content = sanitize(file_content, base_url, links)
        with codecs.open(file_out, 'w+', 'utf-8') as f_out:
            f_out.write(sanitized_content)
            return True
    return False

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run bleach on a source html file')
    parser.add_argument('file_name', metavar='FILE_NAME', help='html target file name')
    args = parser.parse_args()

    file_from = args.file_name
    file_to = make_cleaned_path(file_from)
    sanitize_html_file(file_from, file_to)
