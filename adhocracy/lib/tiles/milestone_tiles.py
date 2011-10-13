from pylons.i18n import _

from adhocracy import model
from adhocracy.lib import text
from adhocracy.lib.tiles.util import render_tile, BaseTile


class MilestoneTile(BaseTile):

    def __init__(self, milestone):
        self.milestone = milestone

    @property
    def text(self):
        if self.milestone.text:
            return text.render(self.milestone.text, escape=False)
        return ""


def row(milestone):
    return render_tile('/milestone/tiles.html', 'row',
                       MilestoneTile(milestone),
                       milestone=milestone, cached=True)


def header(milestone, tile=None):
    if tile is None:
        tile = MilestoneTile(milestone)
    return render_tile('/milestone/tiles.html', 'header',
                       tile, milestone=milestone)


def select(selected, name='milestone'):
    options = [('--', _('(no milestone)'), selected is None)]
    all_future = model.Milestone.all_future()
    # Add the currently selected milestone if it is in the past
    # so it will be shown and won't be overwritten on save
    if (selected is not None) and (selected not in all_future):
        options.append((selected.id, selected.title, True))
    for milestone in all_future:
        options.append((milestone.id, milestone.title,
                        milestone == selected))
    return render_tile('/milestone/tiles.html', 'select',
                       None, options=options, name=name)


def timeline(milestones):
    return render_tile('/milestone/tiles.html', 'timeline',
                       None, milestones=milestones, cached=True)
