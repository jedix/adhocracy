import logging

import formencode
from formencode import validators
from pylons import request, tmpl_context as c
from pylons.i18n import _, lazy_ugettext as L_

from repoze.what.plugins.pylonshq import ActionProtector

from adhocracy import model, forms
from adhocracy.lib.auth.authorization import has_permission
from adhocracy.lib.auth.csrf import RequireInternalRequest
from adhocracy.lib.base import BaseController
from adhocracy.lib.helpers import base_url
from adhocracy.lib.mail import to_user
from adhocracy.lib.templating import render
from adhocracy.lib.util import random_token

log = logging.getLogger(__name__)


class UserImportForm(formencode.Schema):
    allow_extra_fields = True
    #users_csv = forms.UsersCSV()
    users_csv = validators.String(
                    not_empty=True, 
                    messages={'empty' : L_('Please paste a CSV file')})
    send_invite = formencode.validators.StringBool(not_empty=False, if_empty=False,
                                          if_missing=False)
    email_subject = formencode.validators.String(
        messages={'empty': L_('Please insert a subject for the '
                                  'mail we will send to the users.')})
    email_template = forms.ContainsEMailPlaceholders(
            messages={'empty': L_('Please insert a template for the '
                              'mail we will send to the users.')})

    chained_validators = [ forms.UsersCSV() ]

class AdminController(BaseController):

    @ActionProtector(has_permission("global.admin"))
    def index(self):
        return render("/admin/index.html")

    @RequireInternalRequest()
    @ActionProtector(has_permission("global.admin"))
    def permissions(self):
        if request.method == "POST":
            roles = model.Role.all()
            for permission in model.Permission.all():
                for role in roles:
                    t = request.params.get("%s-%s" % (
                            role.code, permission.permission_name))
                    if t and permission not in role.permissions:
                        role.permissions.append(permission)
                    elif not t and permission in role.permissions:
                        role.permissions.remove(permission)
            for role in roles:
                model.meta.Session.add(role)
            model.meta.Session.commit()
        return render("/admin/permissions.html")

    @ActionProtector(has_permission("global.admin"))
    def user_import_form(self, errors=None):
        return formencode.htmlfill.render(render("/admin/import_form.html"),
                                          defaults=dict(request.params),
                                          errors=errors,
                                          force_defaults=False)

    @RequireInternalRequest(methods=['POST'])
    @ActionProtector(has_permission("global.admin"))
    def user_import(self):

        if request.method == "POST":
            try:
                self.form_result = UserImportForm().to_python(request.params)
                # a proposal that this norm should be integrated with
                return self._create_users(self.form_result)
            except formencode.Invalid, i:
                return self.user_import_form(errors=i.unpack_errors())
        else:
            return self.user_import_form()

    def _create_users(self, form_result):
        names = []
        created = []
        mailed = []
        errors = False
        users = []
        log.error(form_result)
        for user_info in form_result['users_csv']:
            try:
                name = user_info['user_name']
                email = user_info['email']

                # optional import columns
                if 'display_name' in form_result['csv_columns']:
                    display_name = user_info['display_name']
                else:
                    display_name = None
                if 'locale' in form_result['csv_columns']:
                    locale = user_info['locale']
                else:
                    locale = None
                if 'password' in form_result['csv_columns']:
                    password = user_info['password']
                else:
                    password = random_token()
                    user_info['password'] = password

                names.append(name)
                user = model.User.create(name, email,
                                         display_name=display_name,
                                         locale=locale,
                                         password=password)
                model.meta.Session.add(user)
                model.meta.Session.commit()
                users.append(user)
                created.append(user.user_name)
                if form_result['send_invite']:
                    user.activation_code = user.IMPORT_MARKER + random_token()
                    url = base_url(c.instance,
                                   path="/user/%s/activate?c=%s" % (
                                       user.user_name,
                                       user.activation_code))

                    user_info['url'] = url
                    body = form_result['email_template'].format(**user_info)
                    to_user(user, form_result['email_subject'], body,
                            decorate_body=False)
                    mailed.append(user.user_name)
                if c.instance:
                    membership = model.Membership(user, c.instance,
                                                  c.instance.default_role)
                    model.meta.Session.expunge(membership)
                    model.meta.Session.add(membership)
                    model.meta.Session.commit()

            except Exception, E:
                log.error('user import for user %s, email %s, exception %s' %
                          (name, email, E))
                errors = True
                continue
        c.users = users
        c.not_created = set(names) - set(created)
        if form_result['send_invite']:
            c.not_mailed = set(created) - set(mailed)
        c.errors = errors
        return render("/admin/import_success.html")
