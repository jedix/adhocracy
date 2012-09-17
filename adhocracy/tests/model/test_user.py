from adhocracy.model import Delegation, Role

from adhocracy.tests import TestController
from adhocracy.tests.testtools import (tt_get_instance, tt_make_proposal,
                                       tt_make_user)


class TestUserController(TestController):

    def test_can_delegate_via_forward_on_user(self):

        proposal = tt_make_proposal(voting=True)

        voter_role = Role.by_code(Role.CODE_VOTER)
        me = tt_make_user(instance_role=voter_role)
        delegate = tt_make_user(instance_role=voter_role)

        Delegation.create(me, delegate, proposal)
        self.assertEqual(delegate.number_of_votes_in_scope(proposal), 2)

    def test_delete_user_deletes_watches(self):
        from adhocracy.model import Watch
        voter_role = Role.by_code(Role.CODE_VOTER)
        user = tt_make_user(instance_role=voter_role)
        instance = tt_get_instance()
        watch = Watch.create(user, instance)
        self.assertFalse(watch.is_deleted())
        user.delete()
        self.assertTrue(watch.is_deleted())
