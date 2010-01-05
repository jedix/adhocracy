import re

from sqlalchemy import Column, Integer, Float, Unicode, UnicodeText, ForeignKey, DateTime, func
from sqlalchemy.orm import relation, synonym, backref

import meta
from meta import Base
import user

class Instance(Base):
    __tablename__ = 'instance'
    
    INSTANCE_KEY = re.compile("^[a-zA-Z][a-zA-Z0-9_]{2,18}$")
    
    id = Column(Integer, primary_key=True)
    _key = Column('key', Unicode(20), nullable=False, unique=True)
    _label = Column('label', Unicode(255), nullable=False)
    description = Column(UnicodeText(), nullable=True)
    
    required_majority = Column(Float, nullable=False)
    activation_delay = Column(Integer, nullable=False)
    
    create_time = Column(DateTime, default=func.now())
    access_time = Column(DateTime, default=func.now(), onupdate=func.now())
    
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relation(user.User, 
        primaryjoin="Instance.creator_id==User.id", 
        backref=backref('created_instances'))
    
    default_group_id = Column(Integer, ForeignKey('group.id'), nullable=True)
    default_group = relation('Group', lazy=True)
        
    root_id = Column(Integer, 
                     ForeignKey('category.id', use_alter=True, name='inst_root_cat'), 
                     nullable=True)
        
    def __init__(self, key, label, creator, description=None):
        self.key = key
        self.label = label
        self.creator = creator
        self.description = description
        self.required_majority = 0.66
        self.activation_delay = 7
        
    def __repr__(self):
        return u"<Instance(%d,%s)>" % (self.id, self.key)
    
    def _get_key(self):
        return self._key
    
    def _set_key(self, value):
        self._key = value.lower()
    
    key = synonym('_key', descriptor=property(_get_key,
                                              _set_key))
    
    def _get_members(self):
        members = []
        for membership in self.memberships:
            if not membership.expire_time:
                members.append(membership.user)
        global_membership = model.Permission.by_code('global-member')
        for group in global_membership.groups:
            for membership in group.memberships:
                if membership.instance == None and not membership.expire_time:
                    members.append(membership.user)
        return members
    
    members = property(_get_members)
    
    def _get_label(self):
        return self._label
    
    def _set_label(self, label):
        self._label = label
        if self.root:
            self.root.label = label
        
    label = synonym('_label', descriptor=property(_get_label,
                                                  _set_label))  
        
    @classmethod
    def find(cls, key, instance_filter=True):
        key = unicode(key.lower())
        try:
            return meta.Session.query(Instance).filter(Instance.key==key).one()
        except: 
            return None
    
    def _index_id(self):
        return self.key
    
    @classmethod  
    def all(cls):
        return meta.Session.query(Instance).all()
        
        
Instance.root = relation('Category', lazy=True,
                    primaryjoin="Instance.root_id==Category.id", 
                    foreign_keys=[Instance.root_id], 
                    uselist=False)