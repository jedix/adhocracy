import logging
from datetime import datetime

from pylons.i18n import _
from formencode import Invalid

from adhocracy.lib.base import *
import adhocracy.forms as forms
import adhocracy.lib.broadcast as broadcast

log = logging.getLogger(__name__)

class AbuseReportForm(formencode.Schema):
    allow_extra_fields = True
    url = validators.String(max=500, not_empty=True)
    message = validators.String(max=20000, min=2, not_empty=True)

class AbuseController(BaseController):
    
    def new(self, format='html', errors={}):
        c.url = request.params.get('url', request.environ.get('HTTP_REFERER'))
        #require.user.message(c.page_user)
        html = render("/abuse/new.html")
        return htmlfill.render(html, defaults=request.params, 
                               errors=errors, force_defaults=False)
    
    @RequireInternalRequest()
    def report(self, format='html'):
        try:
            self.form_result = AbuseReportForm().to_python(request.params)
        except Invalid, i:
            return self.new(errors=i.unpack_errors())
            
        broadcast.notify_abuse(c.instance, c.user, 
            self.form_result.get('url'),
            self.form_result.get('message'))
        h.flash(_("Thank you for helping."), 'notice')
        redirect(self.form_result.get('url'))
