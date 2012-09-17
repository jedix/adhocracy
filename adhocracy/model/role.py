import logging

from sqlalchemy import Table, Column, Integer, Unicode

import meta

log = logging.getLogger(__name__)

role_table = Table('role', meta.data,
    Column('id', Integer, primary_key=True),
    Column('role_name', Unicode(255), nullable=False, unique=True),
    Column('code', Unicode(255), nullable=False, unique=True),
    Column('description', Unicode(1000))
    )


class Role(object):

    CODE_ANONYMOUS = u"anonymous"
    CODE_ORGANIZATION = u"organization"
    CODE_OBSERVER = u"observer"
    CODE_ADVISOR = u"advisor"
    CODE_VOTER = u"voter"
    CODE_SUPERVISOR = u"supervisor"
    CODE_MODERATOR = u"moderator"
    CODE_ADMIN = u"admin"
    CODE_DEFAULT = u"default"

    INSTANCE_ROLES = [CODE_OBSERVER, CODE_VOTER, CODE_SUPERVISOR,
                       CODE_ADVISOR, CODE_MODERATOR]
    INSTANCE_DEFAULT = CODE_VOTER

    def __init__(self, role_name, code, description=None):
        self.role_name = role_name
        self.code = code
        self.description = description

    @classmethod
    def all(cls):
        return meta.Session.query(Role).all()

    @classmethod
    def all_instance(cls):
        # todo: one query.
        return [cls.by_code(g) for g in cls.INSTANCE_ROLES]

    @classmethod
    #@meta.session_cached
    def find(cls, role_name, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Role)
            q = q.filter(Role.role_name == role_name)
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None

    _index_id_attr = 'role_name'

    @classmethod
    #@meta.session_cached
    def by_id(cls, id):
        q = meta.Session.query(Role)
        q = q.filter(Role.id == id)
        return q.limit(1).first()

    @classmethod
    def by_code(cls, code):
        q = meta.Session.query(Role)
        q = q.filter(Role.code == code)
        return q.limit(1).first()

    def __repr__(self):
        return u"<Role(%d,%s)>" % (self.id, self.code)

