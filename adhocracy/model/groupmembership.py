from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, or_
from sqlalchemy import Integer, DateTime, Boolean

import instance_filter as ifilter
import meta

log = logging.getLogger(__name__)


group_membership_table = Table(
    'group_membership', meta.data,
    Column('id', Integer, primary_key=True),
    Column('approved', Boolean, nullable=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('expire_time', DateTime, nullable=True),
    Column('access_time', DateTime, default=datetime.utcnow,
           onupdate=datetime.utcnow),
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False),
    )


class GroupMembership(object):

    def __init__(self, user, group, approved=True):
        self.user = user
        self.group = group
        self.approved = approved

    @classmethod
    def all_q(cls, include_deleted=False):
        q = meta.Session.query(GroupMembership)
        if not include_deleted:
            q = q.filter(or_(GroupMembership.expire_time == None,
                             GroupMembership.expire_time > datetime.utcnow()))
        return q

    @classmethod
    def all(cls, include_deleted=False):
        return cls.all_q(include_deleted=include_deleted).all()

    def expire(self, expire_time=None):
        if expire_time is None:
            expire_time = datetime.utcnow()
        if not self.is_expired(at_time=expire_time):
            self.expire_time = expire_time

    def is_expired(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.expire_time is not None) and \
               self.expire_time <= at_time

    def delete(self, delete_time=None):
        return self.expire(expire_time=delete_time)

    def is_deleted(self, at_time=None):
        return self.is_expired(at_time=at_time)

    def __repr__(self):
        return u"<GroupMembership(%d,%s,%s)>" % (self.id,
                                               self.user.user_name,
                                               self.group.group_name)

