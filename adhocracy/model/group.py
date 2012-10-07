import logging

from sqlalchemy import Table, Column, Integer, Unicode

import meta

log = logging.getLogger(__name__)

group_table = Table('group', meta.data,
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False, unique=True),
    Column('description', Unicode(1000))
    )


class Group(object):

    def __init__(self, group_name, description=None):
        self.group_name = group_name
        self.description = description

    @classmethod
    def all(cls):
        return meta.Session.query(Group).all()

    @classmethod
    #@meta.session_cached
    def find(cls, group_name, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Role)
            q = q.filter(Group.group_name == group_name)
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    _index_id_attr = 'role_name'

    @classmethod
    #@meta.session_cached
    def by_id(cls, id):
        q = meta.Session.query(Group)
        q = q.filter(Group.id == id)
        return q.limit(1).first()

    def __repr__(self):
        return u"<Group(%d,%s)>" % (self.id, self.group_name)

