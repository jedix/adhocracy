from datetime import datetime
import hashlib
import os.path
from time import time

from pylons.i18n import _

from adhocracy.lib.base import *
import adhocracy.lib.text as text
import adhocracy.model.forms as forms
import adhocracy.lib.logo as logo

import adhocracy.lib.instance as libinstance

log = logging.getLogger(__name__)

class InstanceCreateForm(formencode.Schema):
    allow_extra_fields = True
    key = formencode.All(validators.String(min=4, max=20),
                              forms.UniqueInstanceKey())
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    
class InstanceEditForm(formencode.Schema):
    allow_extra_fields = True
    label = validators.String(min=4, max=254, not_empty=True)
    description = validators.String(max=100000, if_empty=None, not_empty=False)
    activation_delay = validators.Int(not_empty=True)
    required_majority = validators.Number(not_empty=True)
    default_group = forms.ValidGroup(not_empty=True)

class InstanceController(BaseController):
    
    @ActionProtector(has_permission("instance.index"))
    def index(self, format='html'):
        h.add_meta("description", _("An index of adhocracies run at adhocracy.cc. " + 
                                    "Select which ones you would like to join and participate in!"))
        instances = model.Instance.all()
        if format == 'json':
            return render_json(instances)
        h.canonical_url(h.instance_url(None, path="/instance"))
        c.instances_pager = pager.instances(instances)
        return render("/instance/index.html")  
    
    
    @ActionProtector(has_permission("instance.create"))
    def new(self):
        return render("/instance/new.html")
    
    
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.create"))
    @validate(schema=InstanceCreateForm(), form="new", post_only=True)
    def create(self):
        instance = model.Instance.create(self.form_result.get('key'), 
                                         self.form_result.get('label'), 
                                         c.user, 
                                         description=self.form_result.get('description'))
        model.meta.Session.commit()
        event.emit(event.T_INSTANCE_CREATE, c.user, instance=instance)    
        redirect(h.entity_url(instance))
    

    @RequireInstance
    @ActionProtector(has_permission("instance.view"))
    def show(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        if format == 'json':
            return render_json(c.page_instance)
        if format == 'rss':
            return self.activity(id, format)
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        tags = model.Tag.popular_tags(limit=70)
        c.tags = sorted(text.tag_cloud_normalize(tags), key=lambda (k, c, v): k.name)
        return render("/instance/show.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("instance.view"))
    def activity(self, id, format='html'):
        c.page_instance = get_entity_or_abort(model.Instance, id)
        
        if format == 'sline':
            sline = event.sparkline_samples(event.instance_activity, c.page_instance)
            return render_json(dict(activity=sline))
        
        events = model.Event.find_by_instance(c.page_instance)
            
        if format == 'rss':
            return event.rss_feed(events, _('%s News' % c.page_instance.label),
                                      h.instance_url(c.page_instance), 
                                      _("News from %s") % c.page_instance.label)
        
        c.tile = tiles.instance.InstanceTile(c.page_instance)
        c.events_pager = pager.events(events)
        return render("/instance/activity.html")
    
    
    @RequireInstance
    @ActionProtector(has_permission("instance.admin"))
    def edit(self, id):
        c.page_instance = self._get_current_instance(id)
        c._Group = model.Group
        default_group = c.page_instance.default_group.code if \
                        c.page_instance.default_group else \
                        model.Group.INSTANCE_DEFAULT
        return htmlfill.render(render("/instance/edit.html"),
                               defaults={
                                    '_method': 'PUT',
                                    'label': c.page_instance.label,
                                    'description': c.page_instance.description,
                                    'required_majority': c.page_instance.required_majority,
                                    'activation_delay': c.page_instance.activation_delay,
                                    'allow_adopt': c.page_instance.allow_adopt,
                                    'default_group': default_group})
        
    
    @RequireInstance
    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("instance.admin"))
    @validate(schema=InstanceEditForm(), form="edit", post_only=True)
    def update(self, id):
        c.page_instance = self._get_current_instance(id)
        c.page_instance.description = text.cleanup(self.form_result.get('description'))
        c.page_instance.label = self.form_result.get('label')
        c.page_instance.required_majority = self.form_result.get('required_majority')
        c.page_instance.activation_delay = self.form_result.get('activation_delay')
        c.page_instance.allow_adopt = self.form_result.get('allow_adopt')
        if self.form_result.get('default_group').code in model.Group.INSTANCE_GROUPS:
            c.page_instance.default_group = self.form_result.get('default_group') 
        
        try:
            if 'logo' in request.POST and hasattr(request.POST.get('logo'), 'file') and \
                request.POST.get('logo').file:
                logo.store(c.page_instance, request.POST.get('logo').file)
        except Exception, e:
            h.flash(unicode(e))
            log.debug(e)
        model.meta.Session.commit()            
        event.emit(event.T_INSTANCE_EDIT, c.user, instance=c.page_instance)
        redirect(h.entity_url(c.page_instance))
    
    
    @ActionProtector(has_permission("instance.index"))
    def icon(self, id, x, y):
        c.page_instance = model.Instance.find(id)
        try:
            (x, y) = (int(x), int(y))
        except ValueError, ve:
            log.debug(ve)
            (x, y) = (24, 24)
        (path, io) = logo.load(c.page_instance, size=(x, y))
        return render_png(io, os.path.getmtime(path))
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.delete"))
    def delete(self, id):
        return self.not_implemented()
    
    
    @RequireInstance
    @RequireInternalRequest()
    @ActionProtector(has_permission("instance.join"))
    def join(self, id):
        c.page_instance = self._get_current_instance(id)
        if c.page_instance in c.user.instances:
            h.flash(_("You're already a member in %(instance)s.") % {
                            'instance': c.page_instance.label})
            redirect('/adhocracies')
        membership = model.Membership(c.user, c.page_instance, 
                                      c.page_instance.default_group)
        model.meta.Session.expunge(membership)
        model.meta.Session.add(membership)
        model.meta.Session.commit()
        
        event.emit(event.T_INSTANCE_JOIN, c.user, 
                   instance=c.page_instance)
        
        h.flash(_("Welcome to %(instance)s") % {
                        'instance': c.page_instance.label})
        return redirect(h.instance_url(c.page_instance))
    
    
    @RequireInstance  
    @RequireInternalRequest()            
    @ActionProtector(has_permission("instance.leave"))
    def leave(self, id):
        c.page_instance = self._get_current_instance(id)
        if not c.page_instance in c.user.instances:
            h.flash(_("You're not a member of %(instance)s.") % {
                            'instance': c.page_instance.label})
        elif c.user == c.page_instance.creator:
            h.flash(_("You're the founder of %s, cannot leave.") % {
                            'instance': c.page_instance.label})
        else:
            for membership in c.user.memberships:
                if membership.is_expired():
                    continue
                if membership.instance == c.page_instance:
                    membership.expire()
                    model.meta.Session.add(membership)
                    
                    democracy.DelegationNode.detach(c.user, c.page_instance)
                    
                    event.emit(event.T_INSTANCE_LEAVE,  c.user, 
                               instance=c.page_instance)
            model.meta.Session.commit()
        redirect('/adhocracies')
    
    
    def _get_current_instance(self, id):
        if id != c.instance.key:
            abort(403, _("You cannot manipulate one instance from within another instance."))
        return c.instance

