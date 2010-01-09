from datetime import datetime

from sqlalchemy import Column, Integer, Unicode, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, backref

# REFACT: use absolute imports to make it easier to see where what comes from
from meta import Base
import user
import meta
import filter as ifilter
import proposal 

class Poll(Base):
    __tablename__ = 'poll'
    
    id = Column(Integer, primary_key=True)
    begin_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    begin_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    begin_user = relation(user.User, 
                          primaryjoin="Poll.begin_user_id==User.id")
    
    proposal_id = Column(Integer, ForeignKey('proposal.id'), nullable=False)
    
    def __init__(self, proposal, begin_user):
        self.proposal = proposal
        self.begin_user = begin_user
    
    def __repr__(self):
        return u"<Poll(%s,%s,%s,%s)>" % (self.id, 
                                         self.proposal_id,
                                         self.begin_time, 
                                         self.end_time)
    
    def _index_id(self):
        return self.id
    
    def end_poll(self, end_time=None):
        if end_time is None:
            end_time = datetime.utcnow()
        if not self.has_ended(at_time=end_time):
            self.end_time = end_time
            
    def has_ended(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.end_time is not None) and \
               self.end_time<=at_time
            
    def delete(self, delete_time=None):
        return self.end_poll(end_time=delete_time)
    
    def is_deleted(self, at_time=None):
        return has_ended(at_time=at_time)
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=True):
        try:
            q = meta.Session.query(Poll)
            if not include_deleted:
                q = q.filter(or_(Poll.end_time==None,
                                 Poll.end_time>datetime.utcnow()))
            q = q.filter(Poll.id==int(id))
            poll = q.one()
            if ifilter.has_instance() and instance_filter:
                poll = poll.proposal.instance == ifilter.get_instance() \
                        and poll or None
            return poll
        except Exception:
            return None
    

Poll.proposal = relation(proposal.Proposal, backref=backref('polls', cascade='all',
                       lazy=False, order_by=Poll.begin_time.desc()))