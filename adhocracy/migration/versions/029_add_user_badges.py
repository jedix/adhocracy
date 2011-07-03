from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import Boolean, DateTime, Integer, Unicode

metadata = MetaData()

badge_table = Table(
    'badge', metadata,
    Column('id', Integer, primary_key=True),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('title', Unicode(40), nullable=False),
    Column('color', Unicode(7), nullable=False),
    Column('description', Unicode(255), nullable=False),
    Column('group_id', Integer, ForeignKey('group.id', ondelete="CASCADE")),
    Column('display_group', Boolean))


user_badges_table = Table('user_badges', metadata,
    Column('id', Integer, primary_key=True),
    Column('badge_id', Integer, ForeignKey('badge.id'),
           nullable=False),
    Column('user_id', Integer, ForeignKey('user.id'),
           nullable=False),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False))


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    group_table = Table('group', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    badge_table.create()
    user_badges_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
