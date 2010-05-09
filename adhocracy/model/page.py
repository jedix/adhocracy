from datetime import datetime
import logging
from itertools import count

from sqlalchemy import Table, Column, Boolean, Integer, Unicode, ForeignKey, DateTime, func, or_
from sqlalchemy.orm import relation, backref

import meta
from delegateable import Delegateable
import instance_filter as ifilter

log = logging.getLogger(__name__)


page_table = Table('page', meta.data,                      
    Column('id', Integer, ForeignKey('delegateable.id'), primary_key=True),
    Column('function', Unicode)
    )


class Page(Delegateable):
    
    DOCUMENT = "document"
    DESCRIPTION = "description"
    NORM = "norm"
    
    FUNCTIONS = [DOCUMENT, DESCRIPTION, NORM]
    WITH_VARIANTS = [NORM] #[DESCRIPTION, NORM]
    
    def __init__(self, instance, alias, creator, function):
        self.init_child(instance, alias, creator)
        self.function = function
        
    
    @classmethod
    def find(cls, id, instance_filter=True, include_deleted=False):
        try:
            q = meta.Session.query(Page)
            try:
                id = int(id)
                q = q.filter(Page.id==id)
            except ValueError:
                q = q.filter(Page.label==id)
            if not include_deleted:
                q = q.filter(or_(Page.delete_time==None,
                                 Page.delete_time>datetime.utcnow()))
            if ifilter.has_instance() and instance_filter:
                q = q.filter(Page.instance==ifilter.get_instance())
            return q.limit(1).first()
        except Exception, e:
            log.warn("find(%s): %s" % (id, e))
            return None


    @classmethod
    def all(cls, instance=None, include_deleted=False):
        q = meta.Session.query(Page)
        if not include_deleted:
            q = q.filter(or_(Page.delete_time==None,
                             Page.delete_time>datetime.utcnow()))
        q = q.filter(Page.instance==instance)
        return q.all()
    
    
    @classmethod
    def free_label(cls, title):
        from adhocracy.lib.text import title2alias
        label = title2alias(title)
        for i in count(0):
            if i == 0: test = label
            else: test = label + str(i)
            page = Page.find(test)
            if page is None: 
                return test
    
    
    @classmethod
    def create(cls, instance, title, text, creator, function=DOCUMENT):
        from text import Text
        if function not in Page.FUNCTIONS:
            raise AttributeError("Invalid page function type")
        label = Page.free_label(title)
        page = Page(instance, label, creator, function)
        meta.Session.add(page)
        meta.Session.flush()
        _text = Text(page, Text.HEAD, creator, title, text)
        return page
        
        
    def establish_variant(self, variant, user):
        for selection in self.selections: 
            selection.make_variant_poll(variant, user)
    
    
    @property
    def proposal(self):
        if self.function == Page.DESCRIPTION:
            return self._proposal[-1]
        return None
    
    
    @property 
    def has_variants(self):
        return self.function in Page.WITH_VARIANTS
    
    
    @property
    def variants(self):
        from text import Text
        if not self.has_variants:
            return [Text.HEAD]
        return list(set([t.variant for t in self.texts]))

        
    def variant_head(self, variant):
        for text in self.texts:
            if text.variant == variant:
                return text
        return None
    
    
    def variant_history(self, variant):
        head = self.variant_head(variant)
        if head:
            return head.history
        return None
        
        
    def variant_comments(self, variant):
        return [c for c in self.comments if (not c.is_deleted()) and c.variant == variant]
    
    
    @property
    def heads(self):
        from text import Text
        if not has_variants:
            return [self.variant_head(Text.HEAD)]
        return [self.variant_head(h) for h in self.variants]
    
    
    @property
    def head(self):
        from text import Text
        return self.variant_head(Text.HEAD)
    
    
    @property
    def title(self):
        return self.head.title
     
    
    @property
    def full_title(self):
        title = self.title
        if self.parent:
            title = self.parent.title + " - " + title
        return title
        
        
    @property
    def parent(self):
        for parent in self.parents:
            if isinstance(parent, Page):
                return parent
        return None
    

    #@property
    #def proposal(self):
    #    from proposal import Proposal
    #    if self.function == Page.DESCRIPTION:
    #        for parent in self.parents:
    #            if isinstance(parent, Proposal):
    #                return parent
    #    return None    
    
    
    def delete(self, delete_time=None):
        if delete_time is None:
            delete_time = datetime.utcnow()
        for text in self.texts:
            text.delete(delete_time=delete_time)
        for selection in self.selections:
            selection.delete(delete_time=delete_time)
        if self.delete_time is None:
            self.delete_time = delete_time
    
    
    def is_deleted(self, at_time=None):
        if at_time is None:
            at_time = datetime.utcnow()
        return (self.delete_time is not None) and \
               self.delete_time<=at_time
    
    
    def is_mutable(self):
        if self.function == self.DESCRIPTION and self.proposal:
            return self.proposal.is_mutable()
        return True
        
    
    def user_position(self, user):
        if self.function == self.DESCRIPTION and self.proposal:
            return self.proposal.user_position(user)
        return 0
    
    
    def _index_id(self):
        return self.id
    
    
    def to_dict(self):
        from adhocracy.lib import url
        d =    dict(id=self.id,
                    url=url.entity_url(self),
                    create_time=self.create_time,
                    label=self.label,
                    head=self.head,
                    function=self.function,
                    user=self.user.user_name)
        if self.parent:
            d['parent'] = self.parent
        return d 
    
    
    def __repr__(self):
        return u"<Page(%s, %s)>" % (self.id, 
                    self.label.encode('ascii', 'ignore'))
    
