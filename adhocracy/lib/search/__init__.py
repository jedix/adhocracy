import logging 
import os, os.path, shutil
from pylons import config

import whoosh

import adhocracy.model as model
import adhocracy.model.hooks as hooks
from .. import util
from .. import queue
from index import open_index, create_index, get_index
import query
from indexers import * 


SITE_INDEX_DIR = ["_index"]

log = logging.getLogger(__name__)

def init_search(with_db=True):
    index_dir = util.get_site_path(*SITE_INDEX_DIR)
    if not os.path.exists(index_dir):
        log.warn("Resetting Whoosh %s index at: %s" % (whoosh.versionstring(), index_dir))
        util.create_site_subdirectory(*SITE_INDEX_DIR)
        create_index(index_dir)
        if with_db:
            rebuild_all()
    else: 
        log.info("Opening Whoosh %s index at: %s" % (whoosh.versionstring(), index_dir))
        open_index(index_dir)
    queue_register()

def register_indexer(cls, index_func):
    queue.register(cls, queue.INSERT, insert(index_func))
    queue.register(cls, queue.UPDATE, update(index_func))
    queue.register(cls, queue.DELETE, delete)

def queue_register():
    register_indexer(model.Proposal, index_proposal)
    register_indexer(model.User, index_user)
    register_indexer(model.Comment, index_comment)
    register_indexer(model.Text, index_text)
    register_indexer(model.Page, index_page)
    
def rebuild_all():
    def index_all(iter, func):
        _insert = update(func)
        [_insert(x) for x in iter]
    try:
        log.info("Re-indexing proposals...")
        index_all(model.meta.Session.query(model.Proposal), index_proposal)
        log.info("Re-indexing users...")
        index_all(model.meta.Session.query(model.User), index_user)
        log.info("Re-indexing comments...")
        index_all(model.meta.Session.query(model.Comment), index_comment)
        log.info("Re-indexing pages...")
        index_all(model.meta.Session.query(model.Page), index_page)
        log.info("Re-indexing texts...")
        index_all(model.meta.Session.query(model.Text), index_text)
        log.info("... done")
    except Exception, e:
        log.exception("Couldn't rebuild index: %s" % e)
    
        
        
            
    