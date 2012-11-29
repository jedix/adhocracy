import logging

import formencode
from formencode import Any, All, htmlfill, Invalid, validators


from pylons import request, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.decorators import validate
from pylons.i18n import _


from adhocracy import model, forms
from adhocracy.lib import helpers as h, search as libsearch, sorting, tiles, pager
from adhocracy.lib.auth import require
from adhocracy.lib.auth.authorization import has_permission

from adhocracy.lib.auth.csrf import RequireInternalRequest
from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy.lib.base import BaseController
from adhocracy.lib.pager import NamedPager
from adhocracy.lib.templating import render, render_json
from adhocracy.lib.util import get_entity_or_abort

from adhocracy.forms.common import ContainsChar

import hashlib

log = logging.getLogger(__name__)


class GroupForm(formencode.Schema):
    allow_extra_fields = True
    group_name = All(validators.String(max=40, not_empty=True),
                ContainsChar())
    description = validators.String(max=255)
    membership_visibility = validators.String(max=40)

class ChangeRoleForm(formencode.Schema):
    allow_extra_fields = False
    instance_id = All()
    role_id = All()

class GroupImportForm(formencode.Schema):
    allow_extra_fields = True
    emails = All(validators.String(not_empty=True))


class DummyInstance():
    def __init__(self, id, label):
        self.id = id
        self.label = label

class GroupController(BaseController):
    base_url_ = None

    @property
    def base_url(self):
        if self.base_url_ is None:
            self.base_url_ = h.site.base_url(instance=c.instance,
                                             path='/group')
        return self.base_url_

    def _redirect_not_found(self, id):
        h.flash(_("We cannot find the group with the id %s") % str(id),
                'error')
        redirect(self.base_url)

    def get_group_or_redirect(self, id):
        '''
        Get a group. Redirect if it does not exist. 
        '''
        group = model.Group.find(id)
        if group is None or not has_permission('group.manage'):
            self._redirect_not_found(id)
        return group

    def index(self, format='html'):
        require.group.index()
        c.base_group_url = self.base_url
        groups = model.Group.all()
        c.group_pager = pager.groups(groups)
        c.groups = sorted(groups, key=lambda group: group.group_name)
        return render("/group/index.html")

    def show(self, group_id):
        group = self.get_group_or_redirect(group_id)
        c.base_group_url = self.base_url
        c.group = group
        c.tile = tiles.group.GroupTile(c.group)
        return render("/group/show.html")
        
    @ActionProtector(has_permission("group.manage"))
    def edit(self, group_id, errors=None):
        group = self.get_group_or_redirect(group_id)
        c.form_type = 'update'
        c.visibility_options = model.Group.MEMBERS_VISIBILITY;
        c.group = group
        c.base_group_url = self.base_url

        defaults = dict(group_name=group.group_name,
                        description=group.description,
                        membership_visibility=group.membership_visibility)

        return htmlfill.render(render("/group/form.html"),
                               errors=errors,
                               defaults=defaults)

    @ActionProtector(has_permission("group.manage"))
    def add(self, errors=None):
        c.form_type = 'add'
        c.visibility_options = model.Group.MEMBERS_VISIBILITY;
        c.base_group_url = self.base_url
        return htmlfill.render(render("/group/form.html"),
                               defaults=dict(request.params),
                               errors=errors)

    @ActionProtector(has_permission("group.manage"))
    def ask_delete(self, group_id):
        c.group = self.get_group_or_redirect(group_id)
        return render('/group/ask_delete.html')

    @ActionProtector(has_permission("group.manage"))
    def delete(self, group_id):
        group = self.get_group_or_redirect(group_id)
        group.delete()
        model.meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(has_permission("group.manage"))
    def members(self, group_id, errors=None):
        group = self.get_group_or_redirect(group_id)
        c.base_group_url = self.base_url
        c.group = group
        c.errors = errors
        #c.group_members = model.User.search(include_group=group.id)
        #c.non_group_members = model.User.search(exclude_group=group.id)
        # With number of users (second query)
        user_limit = 10
        c.group_members = model.User.search(limit=user_limit, include_group=group.id)
        if len(c.group_members) == user_limit:
            c.more_group_members = model.User.search(include_group=group.id, count_only=True) - user_limit
        c.non_group_members = model.User.search(limit=user_limit, exclude_group=group.id)
        if len(c.non_group_members) == user_limit:
            c.more_non_group_members = model.User.search(exclude_group=group.id, count_only=True) - user_limit
        return render("/group/user_form.html")

    @ActionProtector(has_permission("group.manage"))
    def roles(self, group_id, errors=None):
        group = self.get_group_or_redirect(group_id)
        c.base_group_url = self.base_url
        all_instances = [DummyInstance(0, _('all instances'))]
        q = model.Instance.all_q().order_by(model.Instance.label)
        for group_role in group.group_roles:
            if group_role.instance is not None:
                q = q.filter(model.Instance.id != group_role.instance.id)
            else:
                all_instances = []
        c.instances = all_instances + q.all()
        
        c.group = group
        c.roles = model.Role.all()
        return render("/group/role_form.html")

    @ActionProtector(has_permission("group.manage"))
    @RequireInternalRequest()
    def update(self, group_id):
        try:
            self.form_result = GroupForm().to_python(request.params)
        except Invalid, i:
            return self.edit(group_id, i.unpack_errors())

        group = self.get_group_or_redirect(group_id)
        group_name, description, membership_visibility = self._get_common_fields(self.form_result)
        if membership_visibility not in model.Group.MEMBERS_VISIBILITY:
            raise AssertionError('Unknown membership visibility: %s' % membership_visibility)


        group.group_name = group_name
        group.description = description
        group.membership_visibility = membership_visibility
        model.meta.Session.commit()
        h.flash(_("Group changed successfully"), 'success')
        redirect(self.base_url)

    @ActionProtector(has_permission("group.manage"))
    def add_member(self, group_id, user_id, format='html'):
        group = self.get_group_or_redirect(group_id)
        user = model.User.by_id(user_id)
        if user is None:
            if format == 'json':
                return render_json({'message' : _("User does not exist.")})
            h.flash(_("User does not exist."))
            redirect(h.entity_url(group, member='members'))
        if user.is_group_member(group):
            if format == 'json':
                return render_json({'message' : _("User is already member of this group.")})
            else:
                h.flash(_("User is already member of this group."))
                redirect(h.entity_url(group, member='members'))
        group_membership = model.GroupMembership(group, user)
        model.meta.Session.add(group_membership)
        model.meta.Session.commit()
        if format == 'json':
            return render_json({'message' : 'success'})
        redirect(h.entity_url(group, member='members'))


    @ActionProtector(has_permission("group.manage"))
    def remove_member(self, group_id, user_id, format='html'):
        group = self.get_group_or_redirect(group_id)
        delete_membership = model.GroupMembership.find(group_id=group.id, user_id=int(user_id))
        if delete_membership is None:
            if format == 'json':
                return render_json({'message': _("Could not find member in group.")})
            else:
                h.flash(_("Could not find member in group."))
                redirect(h.entity_url(group, member='members'))
        else:
            delete_membership.delete()
            model.meta.Session.commit()
            if format == 'json':
                return render_json({'message': 'success'})
        redirect(h.entity_url(group, member='members'))

    @ActionProtector(has_permission("group.manage"))
    def change_role(self, group_id, instance_id = None, role_id = None, format='html'):
        if instance_id is None or role_id is None:
            try:
                self.form_result = ChangeRoleForm().to_python(request.params)
            except Invalid, i:
                return self.roles(group_id)
            instance_id, role_id = self._get_change_role_fields(self.form_result)

        group = self.get_group_or_redirect(group_id)
        q = model.meta.Session.query(model.Instance)
        q = q.filter(model.Instance.id == instance_id)
        instance = q.limit(1).first()

        if instance is None and instance_id != "0":
            if format == 'json':
                return render_json({'message': _('Could not find instance.')})
            else:
                h.flash(_("Could not find instance."))
        role = model.Role.by_id(role_id)
        if role is None and role_id != "0":
            if format == 'json':
                return render_json({'message': _('Could not find role.')})
            else:
                h.flash("%s %s"%(_("Could not find role."),role_id))

        q = model.meta.Session.query(model.GroupRole)
        if instance is not None: 
            q = q.filter(model.GroupRole.instance_id == instance_id)
        else:
            q = q.filter(model.GroupRole.instance_id == None)
        group_role = q.limit(1).first()

        if group_role is not None:
            if role is None:
                group_role.delete()
            else:
                group_role.role = role
                model.meta.Session.add(group_role)
                model.meta.Session.commit()
        elif role is not None:
            group_role = model.GroupRole(group, role, instance)
            model.meta.Session.add(group_role)
            model.meta.Session.commit()

        if format == 'json':
            return render_json({'message': _('success')})

        redirect(h.entity_url(group, member='roles'))
            
    @ActionProtector(has_permission("group.manage"))
    def create(self, format='html'):
        try:
            self.form_result = GroupForm().to_python(request.params)
        except Invalid, i:
            return self.add(i.unpack_errors())

        group_name, description, membership_visibility = self._get_common_fields(self.form_result)
        if membership_visibility not in model.Group.MEMBERS_VISIBILITY:
            raise AssertionError('Unknown membership visibility: %s' % membership_visibility)
        model.Group.create(group_name, description, membership_visibility)
        model.meta.Session.commit()
        redirect(self.base_url)

    @ActionProtector(has_permission("group.manage"))
    def import_members(self, group_id):
        c.base_group_url = self.base_url
        c.group = self.get_group_or_redirect(group_id)
        return render("/group/import_form.html")

    @ActionProtector(has_permission("group.manage"))
    def do_import(self, group_id):
        group = self.get_group_or_redirect(group_id)
        try:
            self.form_result = GroupImportForm().to_python(request.params)
        except Invalid, i:
            self.import_members(i.unpack_errors())

        emails = self._get_email_list(self.form_result)
        emails_not_found = []
        for email in emails.splitlines():
            user = model.User.find_by_email(email.strip(), True)
            if user is not None:
                if not user.is_group_member(group):
                    group_membership = model.GroupMembership(group, user)
                    model.meta.Session.add(group_membership)
            else:
                emails_not_found.append(email.strip())
        if len(emails) > len(emails_not_found):
            model.meta.Session.commit()
        if len(emails_not_found) == 0:
            emails_not_found = None
        return self.members(group.id, errors=emails_not_found)


    @ActionProtector(has_permission("group.manage"))
    def userlist(self, group_id, type='members', name_filter=None, format='ajax'):
        group = model.Group.find(group_id)
        userlimit = 10
        count = 0
        if group is None:
            return render_json([]);
        userlist = []
        if type == 'members':
            users = model.User.search(name_filter, include_group=group.id, limit=userlimit)
            if len(users) == userlimit:
                count = model.User.search(name_filter, include_group=group.id, count_only=True) - userlimit
        else:
            users = model.User.search(name_filter, exclude_group=group.id, limit=userlimit)
            if len(users) == userlimit:
                count = model.User.search(name_filter, exclude_group=group.id, count_only=True) - userlimit
        for user in users:
            userlist.append([user.id, user.name, user.email, hashlib.md5(user.email.lower()).hexdigest()])
        return render_json([count, userlist])

    def _get_common_fields(self, form_result):
        '''
        return a tuple of (group_name, description).
        '''
        return (form_result.get('group_name').strip(),
                form_result.get('description').strip(),
                form_result.get('membership_visibility').strip())

    def _get_email_list(self, form_result):
        return (form_result.get('emails').strip())

    def _get_change_role_fields(self, form_result):
        return (form_result.get('instance_id'), form_result.get('role_id'))
