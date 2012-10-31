from pylons import tmpl_context as c
from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import text
from adhocracy.lib.tiles.util import render_tile, BaseTile


class GroupTile(BaseTile):

    def __init__(self, group):
        self.group = group

    @property
    def description(self):
        if self.group.description:
            return text.render(self.group.description, escape=False)
        return ""

def row(group):
    if not group:
        return ""
    return render_tile('/group/tiles.html', 'row', GroupTile(group),
                       group=group, cached=True)


def header(group, tile=None, active='activity'):
    if tile is None:
        tile = GroupTile(group)
    return render_tile('/group/tiles.html', 'header', tile,
                       group=group, active=active)
