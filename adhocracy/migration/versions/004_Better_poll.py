from datetime import datetime

from sqlalchemy import *
from migrate import *
import migrate.changeset

meta = MetaData(migrate_engine)

delegateable_table = Table('delegateable', meta,
    Column('id', Integer, primary_key=True),
    Column('label', Unicode(255), nullable=False),
    Column('type', String(50)),
    Column('create_time', DateTime, default=datetime.utcnow),
    Column('access_time', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Column('delete_time', DateTime, nullable=True),
    Column('creator_id', Integer, ForeignKey('user.id'), nullable=False),
    Column('instance_id', Integer, ForeignKey('instance.id'), nullable=False)
    )


def upgrade():
    poll_table_old = Table('poll', meta,
        Column('id', Integer, primary_key=True),
        Column('begin_time', DateTime, default=datetime.utcnow),
        Column('end_time', DateTime, nullable=True),
        Column('begin_user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)   
        )
    
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True)
        )
    
    adopt_poll_id = Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
    adopt_poll_id.create(proposal_table)
    
    action = Column('action', Unicode(50), nullable=False, default='adopt')
    subject = Column('subject', UnicodeText(), nullable=False)
    scope_id = Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
    action.create(poll_table_old)
    subject.create(poll_table_old)
    scope_id.create(poll_table_old)
    poll_table_old.c.begin_user_id.alter(name="user_id")
    
    q = migrate_engine.execute(poll_table_old.select())
    for (id, _, _, _, proposal_id, _, _, _) in q:
        u = poll_table_old.update(id==poll_table_old.c.id, 
                                  {'scope_id': proposal_id,
                                   'subject': u"@[proposal:%s]" % proposal_id,
                                   'action': u'adopt'})
        migrate_engine.execute(u)
        q = proposal_table.update(proposal_table.c.id==proposal_id,
                                  {'adopt_poll_id': id})
        migrate_engine.execute(q)
    
    poll_table_old.c.proposal_id.drop()

def downgrade():
    poll_table_new = Table('poll', meta,
        Column('id', Integer, primary_key=True),
        Column('begin_time', DateTime, default=datetime.utcnow),
        Column('end_time', DateTime, nullable=True),
        Column('user_id', Integer, ForeignKey('user.id'), nullable=False),
        Column('action', Unicode(50), nullable=False),
        Column('subject', UnicodeText(), nullable=False),
        Column('scope_id', Integer, ForeignKey('delegateable.id'), nullable=False)
        ) 
    
    proposal_table = Table('proposal', meta,
        Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
        Column('comment_id', Integer, ForeignKey('comment.id'), nullable=True),
        Column('adopt_poll_id', Integer, ForeignKey('poll.id'), nullable=True)
        )
    
    migrate_engine.execute(poll_table_new.delete())
    poll_table_new.c.action.drop()
    poll_table_new.c.subject.drop()
    poll_table_new.c.scope_id.drop()
    proposal = Column('proposal_id', Integer, ForeignKey('proposal.id'), nullable=False)
    proposal.create(poll_table_new)
    poll_table_new.c.user_id.alter(name="begin_user_id")
    proposal_table.c.adopt_poll_id.drop() 

