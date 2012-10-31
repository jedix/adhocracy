from pylons import tmpl_context as c
from adhocracy.lib.auth.authorization import has


def index(check):
    check.perm('group.show')

def show(check, g):
    check.perm('group.show')

def create(check):
    check.perm('group.manage')

def edit(check, g):
    check.perm('group.manage')

def manage(check, g):
    check.perm('group.manage')

delete = edit
