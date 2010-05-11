from datetime import datetime
from util import render_tile, BaseTile

from pylons import tmpl_context as c
from webhelpers.text import truncate
import adhocracy.model as model

import proposal_tiles
import comment_tiles

from .. import democracy
from .. import helpers as h
from .. import text

from delegateable_tiles import DelegateableTile

class PageTile(DelegateableTile):
    
    def __init__(self, page):
        self.page = page
        DelegateableTile.__init__(self, page)
    
    


def row(page):
    return render_tile('/page/tiles.html', 'row', PageTile(page), 
                       page=page, cached=True)  


def select_page(field_name='page', exclude=[], functions=[], list_limit=20):
    return render_tile('/page/tiles.html', 'select_page', None, exclude=exclude,
                       field_name=field_name, functions=functions, list_limit=list_limit)    


def inline(page, tile=None, text=None):
    if tile is None:
        tile = PageTile(page)
    if text is None:
        text = page.head
    return render_tile('/page/tiles.html', 'inline', tile, page=page, text=text)


def header(page, tile=None, active='goal', text=None, variant=None):
    if tile is None:
        tile = PageTile(page)
    if text is None:
        text = page.head
    if variant is None:
        variant = text.variant
    return render_tile('/page/tiles.html', 'header', tile, 
                       page=page, text=text, variant=variant, active=active)
 
 