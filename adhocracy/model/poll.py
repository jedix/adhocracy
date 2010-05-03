import logging
from datetime import datetime

from sqlalchemy import Table, Column, Integer, Unicode, UnicodeText, ForeignKey, DateTime, func
from sqlalchemy.orm import reconstructor

import meta
import instance_filter as ifilter

log = logging.getLogger(__name__)


poll_table = Table('poll', meta.data,
    Column('id', Integer, primary_key=True),
    Column('begin_time', DateTime, default=datetime.utcnow),
    Column('end_time', DateTime, nullable=True),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('action', Unicode(50), nullable=False),
    Column('subject', UnicodeText(), nullable=False),
    Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
    )

class NoPollException(Exception): pass

class Poll(object):
    
    ADOPT = u'adopt'
    REPEAL = u'repeal'
    RATE = u'rate'
    
    ACTIONS = [ADOPT, REPEAL, RATE]
        
    def __init__(self, scope, user, action, subject=None):
        self.scope = scope
        self.user = user
        if not action in self.ACTIONS:
            raise ValueError("Invalid action!")
        self.action = action
        if subject is None:
            subject = scope
        self._subject_entity = None
        self._tally = None
        self._stable = {}
        self.subject = subject
    
    
    @reconstructor
    def _reconstruct(self):
        self._subject_entity = None
        self._tally = None
        self._stable = {}
    
    
    def _get_subject(self):
        import refs
        if self._subject_entity is None:
            self._subject_entity = refs.to_entity(self._subject)
        return self._subject_entity
    
    
    def _set_subject(self, subject):
        import refs
        self._subject_entity = subject
        self._subject = refs.to_ref(subject)
    
    subject = property(_get_subject, _set_subject)
    
    
    def _get_tally(self):
        if self._tally is None:
            from tally import Tally
            q = self.tallies
            q = q.order_by(Tally.create_time.desc())
            q = q.order_by(Tally.id.desc())
            _tally = q.limit(1).first()
            if _tally is None:
                _tally = Tally.create_from_poll(self)
            self._tally = _tally
        return self._tally
        
    tally = property(_get_tally)
    
    
    def can_end(self):
        if self.has_ended():
            return False
        if self.action == self.RATE:
            return False
        if self.tally.has_majority() and self.tally.has_participation(): 
            return False
        return True
    
    
    def end(self, end_time=None):
        if end_time is None:
            end_time = datetime.utcnow()
        if not self.has_ended(at_time=end_time):
            self.end_time = end_time
    
    
    def has_ended(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()    
        return (self.end_time is not None) \
               and self.end_time<=at_time
    
            
    def delete(self, delete_time=None):
        return self.end(end_time=delete_time)
    
    
    def is_deleted(self, at_time=None):
        return has_ended(at_time=at_time)
        
        
    def check_stable(self, at_time):
        from tally import Tally
        end = datetime.utcnow() if at_time is None else at_time
        start = end - self.scope.instance.activation_timedelta
        tallies = Tally.all_samples(self, start, end)
        if not len(tallies):
            return False
        if tallies[0].create_time > start:
            return False
        for tally in tallies:
            if not (tally.has_participation() and \
                    tally.has_majority()):
                return False
        return True
        
    def is_stable(self, at_time=None):
        if not at_time in self._stable:
            self._stable[at_time] = self.check_stable(at_time)
        return self._stable[at_time]    
    
    
    @classmethod
    def create(cls, scope, user, action, subject=None, with_vote=False):
        from tally import Tally
        from vote import Vote
        from adhocracy.lib.democracy import Decision
        poll = Poll(scope, user, action, subject=subject)
        meta.Session.add(poll)
        meta.Session.flush()
        decision = Decision(user, poll)
        decision.make(Vote.YES)
        Tally.create_from_poll(poll)
        meta.Session.flush()
        return poll
    
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=True):
        from delegateable import Delegateable
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.id==int(id))
            if not include_deleted:
                q = q.filter(or_(Poll.end_time==None,
                                 Poll.end_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.join(Delegateable)
                q = q.filter(Delegateable.instance == ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None
            
            
    @classmethod
    def by_subjects(cls, subjects, instance_filter=True, include_deleted=True):
        from delegateable import Delegateable
        try:
            q = meta.Session.query(Poll)
            q = q.filter(Poll.subject.in_(subjects))
            if not include_deleted:
                q = q.filter(or_(Poll.end_time==None,
                                 Poll.end_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter and poll:
                q = q.join(Delegateable)
                q = q.filter(Delegateable.instance == ifilter.get_instance())
            return q.all()
        except Exception, e:
            log.warn("by_subjects(%s): %s" % (id, e))
            return None
    
    
    def to_dict(self):
        from adhocracy.lib import url
        return dict(id=self.id,
                    user=self.user.user_name,
                    action=self.action,
                    begin_time=self.begin_time,
                    end_time=self.end_time,
                    tally=self.tally,
                    url=url.entity_url(self),
                    scope=self.scope,
                    subject=self.subject)
    
    
    def _index_id(self):
        return self.id
    
        
    def __repr__(self):
        return u"<Poll(%s,%s,%s,%s)>" % (self.id, 
                                         self.scope_id,
                                         self.begin_time, 
                                         self.end_time)
    

