from pylons.i18n import _

from adhocracy.lib.base import *
from adhocracy.model.forms import VoteCastForm

log = logging.getLogger(__name__)

class VoteController(BaseController):
    
    @RequireInstance
    @RequireInternalRequest()
    @validate(schema=VoteCastForm(), form="cast_error", post_only=False, on_get=True)
    def cast(self, id):
        c.poll = get_entity_or_abort(model.Poll, id)
        if not c.poll: 
            abort(404, _("No proposal with ID %(id)s exists.") % {'id': id})
        if not h.has_permission("vote.cast"):
            h.flash(_("You have no voting rights."))
            redirect_to("/proposal/%s" % str(id))
            
        orientation = self.form_result.get("orientation")
        votes = democracy.Decision(c.user, c.poll).make(orientation)
        for vote in votes:
            event.emit(event.T_VOTE_CAST, vote.user, instance=c.instance, 
                       topics=[c.poll.proposal], vote=vote, poll=c.poll)
        redirect_to("/proposal/%s" % str(c.poll.proposal.id))
        
    def cast_error(self, id):
        h.flash(_("Illegal input for vote cast."))
        redirect_to("/proposal/%s" % str(c.poll.proposal.id))
