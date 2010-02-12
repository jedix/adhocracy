"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

import urllib, hashlib, cgi

from pylons import tmpl_context as c
from pylons import request
from pylons.i18n import add_fallback, get_lang, set_lang, gettext, _

import authorization 
from authorization import has_permission_bool as has_permission
import democracy
import cache

import adhocracy.model as model 

from text.i18n import relative_date, relative_time, format_date, countdown_time
from xsrf import url_token, field_token
 
from webhelpers.pylonslib import Flash as _Flash
import webhelpers.text as text
flash = _Flash()

@cache.memoize('delegateable_breadcrumbs')
def breadcrumbs(entity):    
    if not entity:
        return _("Adhocracy")
    
    if isinstance(entity, model.Instance):
        return "<a href='/instance/%s'>%s</a>" % (entity.key, 
                                                  text.truncate(entity.label, length=30, whole_word=True))
    
    link = "<a href='/d/%s'>%s</a>" % (entity.id, text.truncate(entity.label, length=30, whole_word=True))
    if len(entity.parents):
        link = breadcrumbs(entity.parents[0]) + " &raquo; " + link
    else:
        link = breadcrumbs(entity.instance) + " &raquo; " + link
    return link


def immutable_proposal_message():
    return _("This proposal is currently being voted on and cannot be modified.")

@cache.memoize('user_link')
def user_link(user, size=16, scope=None):
    link = "/user/%s" % user.user_name
    score = 0
    if scope:
        score = user.number_of_votes_in_scope(scope)
    return "<a href='%s' class='user_link'><img class='user_icon' src='%s' alt="" /> %s</a><sup>%s</sup>" % (
        instance_url(c.instance, path=link), 
        gravatar_url(user, size=size),
        cgi.escape(user.name),
        score if scope else '')
    
@cache.memoize('proposal_icon', 3600*2)
def proposal_icon(proposal, size=16):
    state = democracy.State(proposal)
    if state.adopted:
        return instance_url(None, path='') + "/img/icons/proposal_adopted_" + str(size) + ".png"
    else:
        return instance_url(None, path='') + "/img/icons/proposal_" + str(size) + ".png"

@cache.memoize('delegateable_link')
def delegateable_link(delegateable, icon=True, icon_size=16, link=True):
    text = ""
    if icon:
        if isinstance(delegateable, model.Proposal):
            text = "<img class='user_icon' src='%s' /> " % proposal_icon(delegateable, size=icon_size)
        elif isinstance(delegateable, model.Issue):
            text = "<img class='user_icon' src='%s/img/icons/issue_%s.png' /> " % (
                        instance_url(None, path=''), icon_size)
    text += cgi.escape(delegateable.label)
    if isinstance(delegateable, model.Proposal) and icon:
        state = democracy.State(delegateable)
        if state.polling:
            text += " <img class='user_icon' src='/img/icons/vote_%s.png' />" % icon_size
    
    if link and not delegateable.delete_time:
        if isinstance(delegateable, model.Proposal):
            text = "<a href='%s' class='dgb_link'>%s</a>" % (
                        instance_url(delegateable.instance, path='/proposal/%s' % delegateable.id), text)
        elif isinstance(delegateable, model.Issue):
            text = "<a href='%s' class='dgb_link'>%s</a>" % (
                        instance_url(delegateable.instance, path='/issue/%s' % delegateable.id), text)
    return text

def contains_delegations(user, delegateable, recurse=True):
    for delegation in user.agencies:
        if not delegation.revoke_time and (delegation.scope == delegateable or \
            (delegation.scope.is_sub(delegateable) and recurse)):
            return True
    for delegation in user.delegated:
        if not delegation.revoke_time and (delegation.scope == delegateable or \
            (delegation.scope.is_sub(delegateable) and recurse)):
            return True
    return False

#default_gravatar = "http://adhocracy.cc/img/icons/user_%s.png"
def gravatar_url(user, size=32):
    # construct the url
    id = user.email if user.email else user.user_name
    gravatar_url = "http://www.gravatar.com/avatar.php?"
    gravatar_url += urllib.urlencode({'gravatar_id':hashlib.md5(id).hexdigest(), 
        'default':'identicon', 
        'size': str(size)})
    return gravatar_url
    
def instance_url(instance, path="/"):
    subdomain = ""
    if instance: # don't ask
        subdomain = instance.key + "."
    return str("http://%s%s%s" % (subdomain,
                               request.environ.get('adhocracy.domain'),
                               path))

def canonical_url(url):
    c.canonical_url = url

def add_meta(key, value):
    if not c.html_meta:
        c.html_meta = dict()
    c.html_meta[key] = value
    
def add_rss(title, link):
    if not c.html_link:
        c.html_link = []
    c.html_link.append({'title': title, 
                        'href': link, 
                        'rel': 'alternate',
                        'type': 'application/rss+xml'})
    
def rss_link(link):
    return "<a class='rss_link' href='%s'><img src='/img/rss.png' /></a>" % link
                                