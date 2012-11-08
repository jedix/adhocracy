import logging

from datetime import datetime
from sqlalchemy import Integer, DateTime, Boolean, String
from sqlalchemy import Table, Column, Integer, Unicode, ForeignKey, or_, and_

import meta

log = logging.getLogger(__name__)

group_table = Table('group', meta.data,
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False),
    Column('description', Unicode(1000)),
    Column('membership_visibility', String(40), default=u"none", nullable=False)
    )

# --[ relation tables ]-----------------------------------------------------
group_membership_table = Table('group_membership', meta.data,
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False, primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False, primary_key=True),
    )

group_roles_table = Table('group_roles', meta.data,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False),
    Column('role_id', Integer, ForeignKey('role.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True),
    )

# --[ Group base classes ]--------------------------------------------------
class Group(object):

    VISIBLE_NONE = u"none"
    VISIBLE_MEMBERS = u"members"
    VISIBLE_ALL = u"all"

    MEMBERS_VISIBILITY = [VISIBLE_NONE, VISIBLE_MEMBERS, VISIBLE_ALL]


    def __init__(self, group_name, description=None, membership_visibility=VISIBLE_NONE):
        self.group_name = group_name
        self.description = description
        self.membership_visibility = membership_visibility

    @classmethod
    def create(cls, group_name, description, membership_visibility):
        group = cls(group_name, description, membership_visibility)
        meta.Session.add(group)
        meta.Session.flush()
        return group

    @classmethod
    def all(cls):
        return meta.Session.query(Group).all()

    @classmethod
    def find(cls, id):
        try:
            q = meta.Session.query(Group)
            id = int(unicode(id).split('-', 1)[0])
            q = q.filter(Group.id == id)
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    _index_id_attr = 'group_name'

    def members(self):
        '''
        return all users that are members of this group
        '''
        members = list(set([membership.user for membership in self.group_memberships]))
        members.sort(key = lambda x: x.name.lower())
        return members

    @classmethod
    #@meta.session_cached
    def by_id(cls, id):
        q = meta.Session.query(Group)
        q = q.filter(Group.id == id)
        return q.limit(1).first()

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    def __repr__(self):
        return u"<Group(%d,%s)>" % (self.id, self.group_name)


class GroupMembership(object):

    def __init__(self, group, user):
        self.group= group
        self.user= user


    @classmethod
    def find(cls, group_id, user_id):
        try:
            q = meta.Session.query(GroupMembership)
            q = q.filter(and_(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id))
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None


    @classmethod
    def all_q(cls):
        q = meta.Session.query(GroupMembership)
        return q

    @classmethod
    def all(cls):
        return cls.all_q().all()

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    def __repr__(self):
        return u"<GroupMembership(%s,%s)>" % (self.group.group_name,
                                           self.user.name)

class GroupRole(object):

    def __init__(self, group, role, instance):
        self.group = group
        self.role = role
        self.instance = instance

    @classmethod
    def all_q(cls):
        q = meta.Session.query(GroupRole)
        return q

    @classmethod
    def all(cls):
        return cls.all_q().all()

    def delete(self):
        meta.Session.delete(self)
        meta.Session.flush()

    def __repr__(self):
        return u"<GroupRole(%s,%s,%s)>" % (self.group.group_name,
                                            self.role.role_name,
                                            self.instance.key)
