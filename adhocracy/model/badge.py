from datetime import datetime
import logging

from sqlalchemy import Table, Column, ForeignKey, and_
from sqlalchemy import Boolean, Integer, DateTime, Unicode

from adhocracy.model import meta
from adhocracy.model import instance_filter as ifilter

log = logging.getLogger(__name__)


badge_table = Table(
    'badge', meta.data,
    #common attributes
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), default=u'', nullable=False),
    #badges for groups/users
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean, default=False),
    #badges for delegateables
    Column('badge_delegateable', Boolean, default=False),
    #badges to make categories for delegateables
    Column('badge_delegateable_category', Boolean, default=False),
    #badges only valid inside an specific instance
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True))


class Badge(object):

    def __init__(self, title, color, description, group=None,
                 display_group=False, badge_delegateable=False,
                 badge_delegateable_category=False, instance=None):
        self.title = title
        self.description = description
        self.color = color
        self.group = group
        self.display_group = display_group
        self.badge_delegateable = badge_delegateable
        self.badge_delegateable_category = badge_delegateable_category
        self.instance = instance

    def __repr__(self):
        return "<Badge(%s,%s)>" % (self.id,
                                   self.title.encode('ascii', 'replace'))

    def __unicode__(self):
        return self.title

    def count(self):
        if self._count is None:
            from badges import Badges
            q = meta.Session.query(Badges)
            q = q.filter(Badges.badge == self)
            self._count = q.count()
        return self._count

    def __le__(self, other):
        return self.title >= other.title

    def __lt__(self, other):
        return self.title > other.title

    @classmethod
    def by_id(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Badge)
            q = q.filter(Badge.id == id)
            return q.limit(1).first()
        except Exception, e:
            log.warn("by_id(%s): %s" % (id, e))
            return None

    @classmethod
    def find(cls, title):
        q = meta.Session.query(Badge)
        try:
            q = q.filter(Badge.id == int(title))
        except ValueError:
            q = q.filter(Badge.title.like(title))
        return q.first()

    @classmethod
    def all_q(cls):
        '''
        A preconfigured query for all Badges ordered by title.
        '''
        return meta.Session.query(Badge).order_by(Badge.title)

    @classmethod
    def all(cls, instance=None):
        """
        Return all badges, orderd by title.
        Without instance it only returns badges not bound to an instance.
        With instance it only returns badges bound to that instance.
        """
        result = cls.all_q().all()
        #TODO do this with SQLAlchemy, "Badge.instance_id == None" does not the job..
        result = [b for b in result if b.instance == instance]
        return result

    @classmethod
    def all_delegateable(cls, instance=None):
        '''
        Return all delegateable badges, ordered by title.
        Without instance it only returns badges not bound to an instance.
        With instance it only returns badges bound to that instance.
        '''
        result = cls.all_q().filter(Badge.badge_delegateable == True).all()
        result = [b for b in result if b.instance == instance]
        return result

    @classmethod
    def all_delegateable_categories(cls, instance=None):
        '''
        Return all badges to make categories for delegateables,
        ordered by title.
        Without instance it only return badges not bound to an instance.
        With instance it only returns badges bound to that instance.
        '''
        result = cls.all_q().filter(Badge.badge_delegateable_category == True).all()
        result = [b for b in result if b.instance == instance]
        return result

    @classmethod
    def all_user(cls, instance=None):
        '''
        Return all user badges, ordered by title.
        Without instance it only return badges not bound to an instance.
        With instance it only returns badges bound to that instance.
        '''
        result = cls.all_q().filter(and_(\
                    Badge.badge_delegateable_category == False,
                    Badge.badge_delegateable == False)).all()
        result = [b for b in result if b.instance == instance]
        return result

    @classmethod
    def create(cls, title, color, description, group=None,
               display_group=False, badge_delegateable=False,
               badge_delegateable_category=False, instance=None):
        badge = cls(title, color, description, group, display_group,
                    badge_delegateable, badge_delegateable_category, instance)
        import ipdb; ipdb.set_trace()
        meta.Session.add(badge)
        meta.Session.flush()
        return badge

    @classmethod
    def find_or_create(cls, title):
        badge = cls.find(title)
        if badge is None:
            badge = cls.create(title)
        return badge

    def to_dict(self):
        return dict(id=self.id,
                    title=self.title,
                    color=self.color,
                    group=self.group and self.group.code or None,
                    display_group=self.display_group,
                    users=[user.name for user in self.users],
                    badge_delegateable=self.badge_delegateable,
                    badge_delegateable_category=self.badge_delegateable_category,
                    instance=self.instance)

    def _index_id(self):
        return self.id
