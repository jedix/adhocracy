from pylons.i18n import _

from adhocracy.lib.base import *

log = logging.getLogger(__name__)

class RootController(BaseController):

    def index(self, format='html'):
        if c.instance: 
            redirect_to('/instance/%s' % str(c.instance.key))
        
        if format == 'rss':
            if c.user:
                # TODO THIS IS A DATA LEAK
                query = model.meta.Session.query(model.Event)
                query = query.filter(model.Event.topics.any([c.issue]+c.issue.motions))
                query = query.filter(model.Event.instance.any(c.user.instances))
                query = query.order_by(model.Event.time.desc())
                query = query.limit(50)  
                return event.rss_feed(query.all(), _('My Adhocracies'),
                                  h.instance_url(None), 
                                  _("Updates from the Adhocracies in which you are a member"))
            else:
                abort(401)
        else:
            c.instances = model.Instance.all()[:5]           
            
        return render('index.html')
    
    #@RequireInstance
    def dispatch_delegateable(self, id):
        dgb = get_entity_or_abort(model.Delegateable, id, instance_filter=False)
        id = str(id)
        
        if isinstance(dgb, model.Category):
            redirect_to(h.instance_url(dgb.instance, path="/category/%s" % id))
        
        if isinstance(dgb, model.Issue):
            redirect_to(h.instance_url(dgb.instance, path="/issue/%s" % id))
        
        redirect_to(h.instance_url(dgb.instance, path="/motion/%s" % id))
        
    def sitemap_xml(self):
        c.delegateables = []
        def add_delegateables(instance):
            children = instance.root.search_children(recurse=True)
            c.delegateables.extend(children)
            
        response.content_type = "text/xml"
        
        if c.instance:
            add_delegateables(c.instance)
        else:
            instances = model.Instance.all()
            for instance in instances:
                add_delegateables(instance)
                
        return render("sitemap.xml")
    
    def process(self):
        event.queue_process()
        return "done."
            