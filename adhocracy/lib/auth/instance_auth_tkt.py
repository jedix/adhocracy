import datetime
import re
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin, _now

# Valid cookie values, see http://tools.ietf.org/html/rfc6265#section-4.1.1
_COOKIE_VALUE_RE = re.compile(u'^[!#$%&\'()*+./0-9:<=>?@A-Z[\\]^_`a-z{|}~-]*$')

class InstanceAuthTktCookiePlugin(AuthTktCookiePlugin):

    def _get_cookies(self, environ, value, max_age=None):
        assert _COOKIE_VALUE_RE.match(value)
        if max_age is not None:
            later = _now() + datetime.timedelta(seconds=int(max_age))
            # Wdy, DD-Mon-YY HH:MM:SS GMT
            expires = later.strftime('%a, %d %b %Y %H:%M:%S')
            # the Expires header is *required* at least for IE7 (IE7 does
            # not respect Max-Age)
            max_age = "; Max-Age=%s; Expires=%s" % (max_age, expires)
        else:
            max_age = ''

        cur_domain = environ.get('adhocracy.domain').split(':')[0]
        wild_domain = '.' + cur_domain

        cookies = [
            ('Set-Cookie', '%s=%s; Path=/; Domain=%s%s' % (
            self.cookie_name, value, wild_domain, max_age))
            ]
        return cookies
