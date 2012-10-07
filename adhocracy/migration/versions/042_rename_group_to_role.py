from sqlalchemy import MetaData, Table, Index
from migrate.changeset.constraint import UniqueConstraint, ForeignKeyConstraint

def upgrade(migrate_engine):
    metadata = MetaData(migrate_engine)

    #define tables
    role_table = Table('group', metadata, autoload=True)
    perm_table = Table('group_permission', metadata, autoload=True)
    instance_table = Table('instance', metadata, autoload=True)
    badge_table = Table('badge', metadata, autoload=True)
    membership_table = Table('membership', metadata, autoload=True)

    #rename constraints
    if migrate_engine.name == "postgresql":
        UniqueConstraint(role_table.c.group_name, name='group_group_name_key').drop()
        UniqueConstraint(role_table.c.group_name, name='role_role_name_key').create()
        ForeignKeyConstraint([instance_table.c.default_group_id], [role_table.c.id], 'instance_default_group_id_fkey').drop()
        ForeignKeyConstraint([instance_table.c.default_group_id], [role_table.c.id], 'instance_default_role_id_fkey').create()
        ForeignKeyConstraint([badge_table.c.group_id], [role_table.c.id], 'badge_group_id_fkey').drop()
        ForeignKeyConstraint([badge_table.c.group_id], [role_table.c.id], 'badge_role_id_fkey').create()
        ForeignKeyConstraint([membership_table.c.group_id], [role_table.c.id], 'membership_group_id_fkey').drop()
        ForeignKeyConstraint([membership_table.c.group_id], [role_table.c.id], 'membership_role_id_fkey').create()
    elif migrate_engine.name == "mysql":
        UniqueConstraint(role_table.c.group_name, name='group_name').drop()
        UniqueConstraint(role_table.c.group_name, name='role_name').create()
        ForeignKeyConstraint([instance_table.c.default_group_id], [role_table.c.id], 'default_group_id').drop()
        ForeignKeyConstraint([instance_table.c.default_group_id], [role_table.c.id], 'default_role_id').create()
        ForeignKeyConstraint([badge_table.c.group_id], [role_table.c.id], 'group_id').drop()
        ForeignKeyConstraint([badge_table.c.group_id], [role_table.c.id], 'role_id').create()
        ForeignKeyConstraint([membership_table.c.group_id], [role_table.c.id], 'group_id').drop()
        ForeignKeyConstraint([membership_table.c.group_id], [role_table.c.id], 'role_id').create()

    #alter and rename table `group`
    role_table.rename('role')
    role_table.c.group_name.alter(name="role_name")

    #alter and rename table `group_permission`
    perm_table.rename('role_permission')
    perm_table.c.group_id.alter(name="role_id")

    #alter table `instance`
    instance_table.c.default_group_id.alter(name="default_role_id")

    #alter table `badge`
    badge_table.c.group_id.alter(name="role_id")
    badge_table.c.display_group.alter(name="display_role")

    #alter table `membership`
    membership_table.c.group_id.alter(name="role_id")


def downgrade(migrate_engine):
    raise NotImplementedError()
