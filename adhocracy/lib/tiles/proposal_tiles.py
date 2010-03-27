from util import render_tile

from pylons import tmpl_context as c
from webhelpers.text import truncate

from .. import democracy
from .. import helpers as h
from .. import text
from ..auth import authorization as auth
from .. import sorting
from .. import cache

from delegateable_tiles import DelegateableTile
from comment_tiles import CommentTile

class ProposalTile(DelegateableTile):
    
    def __init__(self, proposal):
        self.proposal = proposal
        self.__poll = None
        self.__decision = None
        self.__num_principals = None
        self.__comment_tile = None
        DelegateableTile.__init__(self, proposal)
    
    def _tagline(self):       
        if self.proposal.comment and self.proposal.comment.latest:
            tagline = text.plain(self.proposal.comment.latest.text)
            return truncate(tagline, length=140, indicator="...", whole_word=True)
        return ""
    
    tagline = property(_tagline)
    
    def _poll(self):
        if not self.__poll:
            self.__poll = self.proposal.adopt_poll
        return self.__poll
    
    poll = property(_poll)
    
    
    def _position(self):
        @cache.memoize('proposal_position')
        def _cached_position(user, proposal):
            if not user:
                return None
            pos = democracy.Decision(user, proposal.rate_poll).result
            if (pos and pos == 1):
                return "upvoted"
            elif pos and pos == -1:
                return "downvoted"
            return pos
            
        return _cached_position(c.user, self.proposal)
    
    position = property(_position)
    
    
    def _can_edit(self):
        return h.has_permission('proposal.edit') \
                and not self.is_immutable
    
    can_edit = property(_can_edit)    
    
    def _can_delete(self):
        return h.has_permission('proposal.delete') \
                and not self.is_immutable
    
    can_delete = property(_can_delete)
    
    def _can_rate(self):
        return h.has_permission('vote.cast') \
                and self.proposal.rate_poll is not None \
                and not self.proposal.rate_poll.has_ended()
    
    can_rate = property(_can_rate)
    
    def _has_overridden(self):
        if self.decision.is_self_decided():
            return True
        return False
    
    def _can_create_canonical(self):
        return h.has_permission('comment.create') \
                and not self.is_immutable
    
    can_create_canonical = property(_can_create_canonical)
            
    def _is_immutable(self):
        return not self.proposal.is_mutable()
    
    is_immutable = property(_is_immutable)
    
    def _delegates(self):
        agents = []
        if not c.user:
            return []
        for delegation in self.dnode.outbound():
            agents.append(delegation.agent)
        return set(agents)
    
    delegates = property(_delegates)
    
    def _num_principals(self):
        if self.__num_principals == None:
            principals = set(map(lambda d: d.principal, self.dnode.transitive_inbound()))
            if self.poll:
                principals = filter(lambda p: not democracy.Decision(p, self.poll).is_self_decided(),
                                    principals)
            self.__num_principals = len(principals)
        return self.__num_principals
    
    num_principals = property(_num_principals)
    
    def _comment_tile(self):
        if not self.__comment_tile:
            self.__comment_tile = CommentTile(self.proposal.comment)
        return self.__comment_tile
    
    comment_tile = property(_comment_tile)
    
def row(proposal):
    return render_tile('/proposal/tiles.html', 'row', ProposalTile(proposal), 
                       proposal=proposal, cached=True)  

def header(proposal, tile=None, active='goal'):
    if tile is None:
        tile = ProposalTile(proposal)
    return render_tile('/proposal/tiles.html', 'header', tile, 
                       proposal=proposal, active=active)

def sidebar(proposal, tile=None):
   if tile is None:
       tile = ProposalTile(proposal)
   return render_tile('/proposal/tiles.html', 'sidebar', tile, 
                      proposal=proposal)
    