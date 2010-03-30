import cgi
from datetime import datetime

from pylons.i18n import _
from formencode import foreach, Invalid

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.forms as forms
from adhocracy.lib.tiles.proposal_tiles import ProposalTile


log = logging.getLogger(__name__)


class PageCreateForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)

    
class PageUpdateForm(formencode.Schema):
    allow_extra_fields = True
    title = validators.String(max=255, min=4, not_empty=True)
    text = validators.String(max=20000, min=4, not_empty=True)

    
class PageFilterForm(formencode.Schema):
    allow_extra_fields = True
    pages_q = validators.String(max=255, not_empty=False, if_empty=u'', if_missing=u'')


class PageController(BaseController):
    
    @RequireInstance
    @ActionProtector(has_permission("page.view"))
    @validate(schema=PageFilterForm(), post_only=False, on_get=True)
    def index(self, format="html"):
        pages = model.Page.all(instance=c.instance)
        c.pages_pager = pager.pages(pages)
        
        if format == 'json':
            return render_json(c.pages_pager)
            
        return render("/page/index.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("page.create"))
    def new(self, errors=None):
        return render("/page/new.html")
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("page.create"))
    @validate(schema=PageCreateForm(), form='new', post_only=False, on_get=True)
    def create(self, format='html'):
        page = model.Page.create(c.instance, self.form_result.get("title"), 
                                 self.form_result.get("text"), c.user)
        model.meta.Session.commit()
        redirect(h.entity_url(page))


    @RequireInstance
    @ActionProtector(has_permission("page.edit")) 
    def edit(self, id, errors={}):
        c.page = get_entity_or_abort(model.Page, id)
        return render('/page/edit.html')
    
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("page.edit")) 
    @validate(schema=PageUpdateForm(), form='edit', post_only=False, on_get=True)
    def update(self, id, format='html'):
        c.page = get_entity_or_abort(model.Page, id)
        text = model.Text.create(c.page, None, c.user, 
                      self.form_result.get("title"), 
                      self.form_result.get("text"))
        model.meta.Session.commit()
        redirect(h.entity_url(c.page))
    
    
    @RequireInstance
    @ActionProtector(has_permission("page.view"))
    def show(self, id, format='html'):
        c.page = get_entity_or_abort(model.Page, id)
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/show.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("page.delete"))
    def ask_delete(self, id):
        c.page = get_entity_or_abort(model.Page, id)
        c.tile = tiles.page.PageTile(c.page)
        return render("/page/ask_delete.html")
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("page.delete"))
    def delete(self, id):
        c.page = get_entity_or_abort(model.Page, id) 
        c.page.delete()
        model.meta.Session.commit()
        h.flash(_("The page %s has been deleted.") % c.page.title)
        redirect(h.entity_url(c.page.instance))
    
    
    def _common_metadata(self, page):
        pass
