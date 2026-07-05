ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr', 'pre', 'blockquote', 'code', 'kbd', 'samp', 'var',
    'b', 'i', 'u', 's', 'del', 'ins', 'em', 'strong', 'mark',
    'small', 'sub', 'sup', 'abbr', 'cite', 'q', 'dfn', 'time',
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',
    'a', 'img',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
    'div', 'span', 'section', 'article', 'aside', 'header', 'footer',
    'main', 'nav', 'figure', 'figcaption', 'details', 'summary',
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'title', 'lang', 'dir', 'aria-label',
          'aria-describedby', 'aria-hidden', 'role'],
    'a': ['href', 'title', 'target', 'rel', 'download', 'hreflang'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'loading', 'srcset', 'sizes'],
    'th': ['scope', 'colspan', 'rowspan', 'headers'],
    'td': ['colspan', 'rowspan', 'headers'],
    'col': ['span'],
    'colgroup': ['span'],
    'time': ['datetime'],
    'abbr': ['title'],
    'q': ['cite'],
    'blockquote': ['cite'],
    'del': ['cite', 'datetime'],
    'ins': ['cite', 'datetime'],
    'details': ['open'],
    'div': ['align'],
    'p': ['align'],
    'h1': ['align'], 'h2': ['align'], 'h3': ['align'],
    'h4': ['align'], 'h5': ['align'], 'h6': ['align']
}

ALLOWED_PROTOCOLS = [
    'http',
    'https',
    'mailto',
    'tel',
    'sms',
    'ftp',
    'sftp',
    '#',
]