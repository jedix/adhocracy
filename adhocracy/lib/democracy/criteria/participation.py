from criterion import Criterion
from ..decision import Decision

class ParticipationCriterion(Criterion):
    """
    Check to see if the required number of participants have voted
    in a poll. 
    
    The required number is established as the required majority's part
    of the average participation in the given instance.
    """
        
    def _get_required(self):
        return max(1, int(Decision.average_decisions(self.motion.instance) \
                   * self.motion.instance.required_majority))
    
    required = property(_get_required)
    
    def check_tally(self, tally):
        return len(tally) >= self.required
    