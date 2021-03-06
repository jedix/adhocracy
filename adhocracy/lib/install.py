import logging

from adhocracy.lib import helpers as h
import adhocracy.model as model

log = logging.getLogger(__name__)

ADMIN = u'admin'
ADMIN_PASSWORD = u'password'



def mk_role(name, code):
    role = model.Role.by_code(unicode(code))
    if not role:
        log.debug("Creating role: %s" % name)
        role = model.Role(unicode(name), unicode(code))
        model.meta.Session.add(role)
    else:
        role.role_name = unicode(name)
    return role



def mk_perm(name, *roles):
    perm = model.Permission.find(name)
    if perm is None:
        log.debug("Creating permission: %s" % name)
        perm = model.Permission(name)
        model.meta.Session.add(perm)
    perm.roles = list(roles)
    return perm


def setup_entities(initial_setup):
    #model.meta.Session.begin()
    model.meta.Session.commit()

    # administrate installation wide
    admins = mk_role("Administrator", model.Role.CODE_ADMIN)
    organization = mk_role("Organization", model.Role.CODE_ORGANIZATION)
    # administrate instance
    supervisor = mk_role("Supervisor", model.Role.CODE_SUPERVISOR)
    moderator = mk_role("Moderator", model.Role.CODE_MODERATOR)
    voter = mk_role("Voter", model.Role.CODE_VOTER)
    observer = mk_role("Observer", model.Role.CODE_OBSERVER)
    advisor = mk_role("Advisor", model.Role.CODE_ADVISOR)
    default = mk_role("Default", model.Role.CODE_DEFAULT)
    anonymous = mk_role("Anonymous", model.Role.CODE_ANONYMOUS)
    addressee = mk_role("Addressee", model.Role.CODE_ADDRESSEE)

    model.meta.Session.commit()

    if initial_setup:

        # ADD EACH NEW PERMISSION HERE
        mk_perm("comment.create", advisor)
        mk_perm("comment.delete", moderator)
        mk_perm("comment.edit", advisor)
        mk_perm("comment.show", anonymous)
        mk_perm("comment.view", anonymous)
        mk_perm("delegation.create", voter)
        mk_perm("delegation.delete", voter)
        mk_perm("delegation.show", anonymous)
        mk_perm("delegation.view", anonymous)
        mk_perm("global.admin", admins)
        mk_perm("global.member", admins)
        mk_perm("global.organization", organization)
        mk_perm("group.manage", admins)
        mk_perm("group.show", anonymous)
        mk_perm("instance.admin", supervisor)
        mk_perm("instance.create", admins)
        mk_perm("instance.delete", admins)
        mk_perm("instance.index", anonymous)
        mk_perm("instance.join", default)
        mk_perm("instance.leave", default)
        mk_perm("instance.news", anonymous)
        mk_perm("instance.show", anonymous)
        mk_perm("milestone.create", supervisor)
        mk_perm("milestone.delete", supervisor)
        mk_perm("milestone.edit", supervisor)
        mk_perm("milestone.show", anonymous)
        mk_perm("page.create", advisor)
        mk_perm("page.delete", moderator)
        mk_perm("page.edit", advisor)
        mk_perm("page.show", anonymous)
        mk_perm("page.view", anonymous)
        mk_perm("poll.create", moderator)
        mk_perm("poll.delete", moderator)
        mk_perm("poll.show", anonymous)
        mk_perm("proposal.create", advisor)
        mk_perm("proposal.delete", moderator)
        mk_perm("proposal.edit", advisor)
        mk_perm("proposal.show", anonymous)
        mk_perm("proposal.view", anonymous)
        mk_perm("tag.create", advisor)
        mk_perm("tag.delete", advisor)
        mk_perm("tag.show", anonymous)
        mk_perm("tag.view", anonymous)
        mk_perm("user.edit", default)
        mk_perm("user.manage", admins)
        mk_perm("user.message", advisor)
        mk_perm("user.show", anonymous)
        mk_perm("user.view", anonymous)
        mk_perm("vote.cast", voter)
        mk_perm("vote.prohibit", organization)
        mk_perm("watch.create", observer)
        mk_perm("watch.delete", observer)
        mk_perm("watch.show", anonymous)

        model.meta.Session.commit()
        # END PERMISSIONS LIST

        observer.permissions = observer.permissions + anonymous.permissions
        advisor.permissions = advisor.permissions + observer.permissions
        voter.permissions = voter.permissions + advisor.permissions
        moderator.permissions = moderator.permissions + voter.permissions
        supervisor.permissions = list(set(supervisor.permissions
                                   + moderator.permissions + advisor.permissions))
        admins.permissions = admins.permissions + supervisor.permissions
        organization.permissions = organization.permissions + observer.permissions
        addressee.permissions = voter.permissions

    admin = model.User.find(u"admin")
    created_admin = False
    if not admin:
        created_admin = True
        admin = model.User.create(ADMIN, u'',
                                  password=ADMIN_PASSWORD,
                                  global_admin=True)

    model.meta.Session.commit()

    from pylons import config
    if config.get('adhocracy.instance'):
        model.Instance.create(config.get('adhocracy.instance'),
                              u"Adhocracy", admin)
    elif not model.Instance.find(u"test"):
        model.Instance.create(u"test", u"Test Instance", admin)

    model.meta.Session.commit()
