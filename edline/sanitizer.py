import cgi
import codecs
import os
import re
import sys

# Find patched bleach module
sys.path.append(os.path.join(os.path.dirname(__file__), '../../bleach'))
from bleach import clean

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

def sanitize(content):
    i = content.index('<body>') + 6
    j = content.index('</body>')
    body = clean(content[i:j],
        tags=MY_ALLOWED_TAGS, attributes=MY_ALLOWED_ATTRIBUTES,
        styles=MY_ALLOWED_STYLES, strip=True, strip_comments=True)
    body = swap_entities(body)
    body = remove_empty_ps(body)
    html = content[0:i] + body + content[j:]
    return html

def sanitize_html_file(file_in, file_out):
    with codecs.open(file_in, 'r', 'utf-8') as f_in:
        file_content = f_in.read()
        sanitized_content = sanitize(file_content)
        with codecs.open(file_out, 'w+', 'utf-8') as f_out:
            f_out.write(sanitized_content)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run bleach on a source html file')
    parser.add_argument('file_name', metavar='FILE_NAME', help='html target file name')
    args = parser.parse_args()

    file_from = args.file_name
    dirname, basename = os.path.split(file_from)

    dirparent = os.path.dirname(dirname)
    dirname = os.path.join(dirparent, 'cleaned')
    try:
        os.makedirs(dirname)
    except:
        pass
    file_to = os.path.join(dirname, basename)
    sanitize_html_file(file_from, file_to)
