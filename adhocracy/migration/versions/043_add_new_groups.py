from datetime import datetime

from sqlalchemy import MetaData, Column, ForeignKey, Table
from sqlalchemy import DateTime, Integer, Unicode

metadata = MetaData()

group_table = Table('group', metadata,
    Column('id', Integer, primary_key=True),
    Column('group_name', Unicode(255), nullable=False),
    Column('description', Unicode(1000)),
    Column('membership_visibility', Unicode(40), default=u"none", nullable=False)
    )

group_membership_table = Table('group_membership', metadata,
    Column('user_id', Integer, ForeignKey('user.id'), nullable=False, primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False, primary_key=True),
    )

group_roles_table = Table('group_roles', metadata,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey('group.id'), nullable=False),
    Column('role_id', Integer, ForeignKey('role.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=True),
    )


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    role_table = Table('role', metadata, autoload=True)
    user_table = Table('user', metadata, autoload=True)
    instance_table = Table('instance', metadata, autoload=True)
    group_table.create()
    group_membership_table.create()
    group_roles_table.create()


def downgrade(migrate_engine):
    raise NotImplementedError()
