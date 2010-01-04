from datetime import datetime
import time
from nose.tools import *

from adhocracy.model import Poll
from adhocracy.lib.democracy import Decision, DelegationNode
import adhocracy.model as model

from adhocracy.tests import *
from adhocracy.tests.testtools import *


class TestDecisionWithoutDelegation(TestController):
    
    def setUp(self):
        self.motion = tt_make_motion(voting=True)
        self.poll = Poll(self.motion, self.motion.creator)
        self.decision = Decision(self.motion.creator, self.poll)
    
    def test_new_decisions_have_no_votes(self):
        assert_equals(len(self.decision.votes), 0)
        assert_equals(len(self.decision.relevant_votes), 0)
        assert_equals(self.decision.result, None, "Not voted yet == not recorded for quorum")
    
    def test_new_decisions_are_not_decided(self):
        assert_false(self.decision.is_decided())
        assert_false(self.decision.is_self_decided())
    
    def test_can_vote_directly(self):
        self.decision.make(model.Vote.AYE)
        assert_equals(self.decision.result, model.Vote.AYE)
    
    def test_decision_with_a_vote_is_decided(self):
        self.decision.make(model.Vote.AYE)
        assert_true(self.decision.is_decided())
        assert_true(self.decision.is_self_decided())
    
    def test_can_override_previous_choice(self):
        self.decision.make(model.Vote.AYE)
        assert_equals(self.decision.result, model.Vote.AYE)
        self.decision.make(model.Vote.ABSTAIN)
        assert_equals(self.decision.result, model.Vote.ABSTAIN)
        self.decision.make(model.Vote.NAY)
        assert_equals(self.decision.result, model.Vote.NAY)
    
    def test_direct_votes_always_have_only_one_relevant_vote(self):
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.NAY)
        self.decision.make(model.Vote.ABSTAIN)
        assert_equals(len(self.decision.relevant_votes), 1)
    
    # History access
    
    def test_multiple_votes_for_one_decision_are_recorded_for_posterity(self):
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.AYE)
        assert_equals(len(self.decision.votes), 2)
    
    def test_old_decisions_can_be_retrieved(self):
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.AYE)
        self.decision.make(model.Vote.NAY)
        # votes are FIFO
        assert_equals(self.decision.votes[0].orientation, model.Vote.NAY)
        assert_equals(self.decision.votes[1].orientation, model.Vote.AYE)
        assert_equals(self.decision.votes[2].orientation, model.Vote.AYE)
    

class TestDecisionWithDelegation(TestController):
    
    def setUp(self):
        self.user1 = tt_make_user()
        self.user2 = tt_make_user()
        self.user3 = tt_make_user()
        self.motion = tt_make_motion(creator=self.user1, voting=True)
        self.poll = Poll(self.motion, self.user1)
        self.decision = Decision(self.user1, self.poll)
        self.instance = tt_get_instance()
    
    def test_can_do_general_delegate_to_other_user(self):
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user2, scope=self.instance.root)
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        assert_equals(self.decision.reload().result, model.Vote.AYE)
    
    def test_issue_delegation_will_override_root_delegation(self):
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user2, scope=self.instance.root)
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        assert_equals(self.decision.reload().result, model.Vote.AYE)
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user3, scope=self.motion.issue)
        Decision(self.user3, self.poll).make(model.Vote.NAY)
        assert_equals(self.decision.reload().result, model.Vote.NAY)
    
    def test_motion_delegation_will_overide_issue_delegation(self):
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user2, scope=self.motion.issue)
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        assert_equals(self.decision.reload().result, model.Vote.AYE)
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user3, scope=self.motion)
        Decision(self.user3, self.poll).make(model.Vote.NAY)
        assert_equals(self.decision.reload().result, model.Vote.NAY)
    
    def test_two_delegations_at_the_same_level_that_disagree_cancel_each_other(self):
        # This is meant as a safeguard: if I don't fully trust my delegates
        # I can delegate to two, and my vote will only be autocast if they agree.
        # If not, I need to decide myself
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user2, scope=self.motion)
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user3, scope=self.motion)
        Decision(self.user3, self.poll).make(model.Vote.NAY)
        assert_equals(self.decision.reload().result, None, "needs to cast his own vote")
    
    def test_two_delegations_at_the_same_level_that_agree_reinforce_each_other(self):
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user2, scope=self.motion)
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user3, scope=self.motion)
        Decision(self.user3, self.poll).make(model.Vote.AYE)
        assert_equals(self.decision.reload().result, model.Vote.AYE)
    
    def test_own_vote_overrides_delegations(self):
        DelegationNode.create_delegation(from_user=self.user1, to_user=self.user2, scope=self.motion)
        Decision(self.user2, self.poll).make(model.Vote.AYE)
        self.decision.make(model.Vote.NAY)
        assert_equals(self.decision.reload().result, model.Vote.NAY)
    
    # TODO: can access history of delegation decisions
    # TODO: relevant_votes and votes make sense
    
    # def dont_test_something(self):
    #     assert_equals(len(decision.relevant_votes), 1)
    #     assert_equals(len(decision.votes), 0)

# TODO: special case: two delegations with different votes should cancel
# TODO: delegated case can be decided by the delegator or by the user itself
# TODO: delegated an isue to a user and again a motion inside that issue to the same user: make sure he only gets the right ammount of delegations
