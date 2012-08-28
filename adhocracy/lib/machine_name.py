
import platform
from webob import Request, Response

class IncludeMachineName(object):
    
    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        # Nested function to add the X-Server-Machine header
        def local_response(status, headers, exc_info=None):
            headers.append(('X-Server-Machine', platform.node()))
            start_response(status, headers, exc_info)
        return self.app(environ, local_response)
