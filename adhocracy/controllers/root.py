from datetime import datetime
from pylons.i18n import _

from adhocracy.lib.base import *
from proposal import ProposalFilterForm

log = logging.getLogger(__name__)

class RootController(BaseController):

    @validate(schema=ProposalFilterForm(), post_only=False, on_get=True)
    def index(self, format='html'):
        require.proposal.index()
        if c.instance: 
            redirect(h.entity_url(c.instance))
        
        c.instances = model.Instance.all()[:5]           
        c.page = StaticPage('index')

        query = self.form_result.get('proposals_q')
        proposals = libsearch.query.run(query, entity_type=model.Proposal)[:10]

        c.proposals_pager = pager.proposals(proposals)
	c.proposals = c.proposals_pager.here()

        if format == 'json':
            return render_json(c.proposals_pager)
        return render('index.html')
    
    
    #@RequireInstance
    def dispatch_delegateable(self, id):
        dgb = get_entity_or_abort(model.Delegateable, id, instance_filter=False)
        redirect(h.entity_url(dgb))
    
    
    def sitemap_xml(self):
        if c.instance: 
            redirect(h.base_url(None, path="/sitemap.xml"))
        c.delegateables = model.Delegateable.all()
        c.change_time = datetime.utcnow()
        response.content_type = "text/xml"
        return render("sitemap.xml")
    
    
    def robots_txt(self):
        response.content_type = "text/plain"
        if not c.instance:
            return render("robots.txt")
        return render("instance/robots.txt")
        
            
