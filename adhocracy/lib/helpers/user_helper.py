import cgi 
import urllib 
import hashlib

from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy.lib import democracy
from adhocracy.lib import cache

import url as _url


@cache.memoize('user_icon')
def icon_url(user, size=32):
    id = user.email if user.email else user.user_name
    gravatar_url = "http://www.gravatar.com/avatar.php?"
    gravatar_url += urllib.urlencode({
        'gravatar_id': hashlib.md5(id).hexdigest(), 
        'default': 'identicon', 
        'size': str(size)})
    return gravatar_url


def link(user, size=16, scope=None):
    @cache.memoize('user_generic_link')
    def _generic_link(user, instance, size, scope):
        _url = u"<a href='%s' class='user_link'><img width='16' height='16' class='user_icon' src='%s' alt="" /> %s</a>" % (
            url(user), icon_url(user, size=size), cgi.escape(user.name))
        if scope and ((not c.instance) or c.instance.allow_delegate):
            votes = user.number_of_votes_in_scope(scope)
            if votes > 0:
                _url += u"<sup>%s</sup>" % votes
        return _url

    @cache.memoize('user_specific_link')
    def _specific_link(user, instance, size, scope, other):
        from adhocracy.lib.helpers import entity_url
        url = _generic_link(user, instance, size, scope)
        if other and scope:
            dnode = democracy.DelegationNode(other, scope)
            for delegation in dnode.outbound():
                if delegation.agent == user:
                    icon = u"<img class='user_icon' width='16' height='16' src='/img/icons/delegate_16.png' />"
                    url += u"<a href='%s'>%s</a>" % (entity_url(delegation), icon)
        return url

    return _specific_link(user, c.instance, size, scope, c.user)
    

def url(user, instance=None, **kwargs):
    instance = c.instance if not instance else instance
    @cache.memoize('user_url')
    def furl(user, instance=None, **kwargs):
        return _url.build(instance, 'user', user.user_name, **kwargs)
    return furl(user, instance, **kwargs)


def breadcrumbs(user):
    @cache.memoize('user_bc')
    def fbreadcrumbs(user, instance):
        bc = _url.root()
        bc += _url.link(_("Users"), u'/user')
        if user is not None:
            bc += _url.BREAD_SEP + _url.link(user.name, url(user))
        return bc
    return fbreadcrumbs(user, c.instance)