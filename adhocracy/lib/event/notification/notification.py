import os.path 
import logging 

from pylons import config

from ...text import i18n
from ...templating import render
from .. import formatting

log = logging.getLogger(__name__)

class Notification(object):
    
    TPL_PATTERN = os.path.join("%s", 'adhocracy', 'templates', '%s') 
    TPL_NAME = "/notifications/%s.%s.txt"
    
    def __init__(self, event, user, type=None, watch=None):
        self.event = event
        self._type = type
        self.user = user
        self.watch = watch
        
    def get_type(self):
        if not self._type:
            self._type = self.event.event
        return self._type
        
    type = property(get_type)

    def get_priority(self):
        return self.type.priority
        
    priority = property(get_priority)
    
    def get_id(self):
        return "n-e%s-u%s" % (self.event.id, self.user.id)
    
    id = property(get_id)
    
    def language_context(self):
        return i18n.user_language(self.user)
    
    def get_subject(self):
        formatting.FormattedEvent(self.event, lambda f, value: f.unicode(value))
        return self.type.subject() % data
    
    subject = property(get_subject)
    
    def get_body(self):
        locale = self.language_context()
        tpl_vars = {'n': self, 'e': self.event, 'u': self.user, 't': self.type}
        
        # HACK 
        tpl_name = self.TPL_NAME % (str(self.type), locale.language[0:2])
        tpl_path = self.TPL_PATTERN % (config.get('here'), tpl_name) 
        
        if not os.path.exists(tpl_path):
            log.warn("Notification body needs to be localized to file %s" % (tpl_path)) 
            tpl_name = self.TPL_NAME % (str(self.type), i18n.DEFAULT.language[0:2])
        
        return render(tpl_name, extra_vars=tpl_vars).strip()
    
    body = property(get_body)
            
    def __repr__(self):
        return "<Notification(%s,%s,%s)>" % (self.type, self.user.user_name, self.priority)
    