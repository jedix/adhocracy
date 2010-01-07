import logging
import simplejson 
from datetime import datetime

from pylons.i18n import _

from adhocracy.lib.base import *
from adhocracy.lib.karma import *
import adhocracy.model.forms as forms

log = logging.getLogger(__name__)

class KarmaGiveForm(formencode.Schema):
    allow_extra_fields = True
    comment = forms.ValidComment(not_empty=True)
    value = validators.Int(min=-1, max=1, not_empty=True)

class KarmaController(BaseController):

    @RequireInstance
    @ActionProtector(has_permission("karma.give"))
    @validate(schema=KarmaGiveForm(), post_only=False, on_get=True)
    def give(self, format="html"):
        comment = self.form_result.get('comment')
        value = self.form_result.get('value')
        if not value in [1, -1]:
            h.flash(_("Invalid karma value. Karma is either positive or negative!"))
            redirect_to("/comment/r/%s" % comment.id)
        
        if not c.user == comment.creator:
            karma = position(comment, c.user)
            if karma: 
                karma.value = value
                karma.create_time = datetime.utcnow()
            else:
                karma = model.Karma(value, c.user, comment.creator, comment)
        
            model.meta.Session.add(karma)
            model.meta.Session.commit()
        
        if format == 'json':
            return simplejson.dumps({'score': comment_score(comment)})
            
        redirect_to("/comment/r/%s" % comment.id)
