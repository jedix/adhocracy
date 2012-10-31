from pylons import tmpl_context as c
from adhocracy.lib.helpers import url as _url
from adhocracy.lib.text import label2url
import hashlib 

def gravatar(mail, size=20):
    return 'https://www.gravatar.com/avatar/%s?s=%d'%(hashlib.md5(mail).hexdigest(), size)

def url(group, **kwargs):
    ext = str(group.id) + '-' + label2url(group.group_name)
    return _url.build(None, 'group', ext, **kwargs)

def breadcrumbs(instance):
    bc = _url.root()
    return bc
