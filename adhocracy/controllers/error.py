import cgi
import re

from pylons import request, response, session, tmpl_context as c
from pylons.i18n import _
from adhocracy.lib.base import BaseController, render

from paste.urlparser import PkgResourcesParser
from pylons import request
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from adhocracy.lib.base import BaseController

BODY_RE = re.compile("<br \/><br \/>(.*)<\/body", re.S)

class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    def document(self):
        resp = request.environ.get('pylons.original_response')
        
        # YOU DO NOT SEE THIS. IF YOU DO, ITS NOT WHAT IT LOOKS LIKE
        # I DID NOT HAVE REGEX RELATIONS WITH THAT HTML PAGE
        for match in BODY_RE.finditer(resp.body):
            c.error_message = match.group(1)
        
        c.error_code = cgi.escape(request.GET.get('code', str(resp.status_int)))
        
        if not c.error_message:
            c.error_message = _("Error %s") % c.error_code
        
        response.status = resp.status
        return render("/error/http.html")
    
    
    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))
    
    
    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))
    
    
    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))

