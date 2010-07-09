import math
from datetime import datetime
from util import timedelta2seconds
import event.stats as estats

def delegateable_label(entities):
    return sorted(entities, key=lambda e: e.label.lower())

def instance_label(entities):
    return sorted(entities, key=lambda e: e.label.lower())

def delegateable_title(entities):
    return sorted(entities, key=lambda e: e.title.lower())

def delegateable_full_title(entities):
    return sorted(entities, key=lambda e: e.full_title.lower())

def delegateable_latest_comment(entities):
    return sorted(entities, key=lambda e: e.find_latest_comment_time(), 
                  reverse=True)
                  
def score_and_freshness_sorter(max_age):
    def _with_age(poll, time):
        freshness = 1
        if poll.tally.score > -1:
            age = timedelta2seconds(datetime.utcnow() - time)
            freshness = max(1, math.log10(max(1, max_age - age)))
        return (freshness * poll.tally.score, time)
    return _with_age
                                
def proposal_support(entities):
    max_age = 3600 * 36 # 2 days
    p_key = lambda p: score_and_freshness_sorter(max_age)(p.rate_poll, p.create_time)
    return sorted(entities, key=p_key, reverse=True)
    
def comment_order(comments):
    max_age = 84600 / 2 # 0.5 days
    p_key = lambda c: score_and_freshness_sorter(max_age)(c.poll, c.create_time)
    return sorted(comments, key=p_key, reverse=True)

def user_name(entities):
    return sorted(entities, key=lambda e: e.name.lower())

def entity_newest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=True)

def entity_oldest(entities):
    return sorted(entities, key=lambda e: e.create_time, reverse=False)

def entity_stable(entities):
    return entities

def issue_activity(issues):
    return sorted(issues, key=lambda i: estats.issue_activity(i), 
                  reverse=True)

def proposal_activity(proposals):
    return sorted(proposals, key=lambda m: estats.proposal_activity(m), 
                  reverse=True)

def instance_activity(instances):
    return sorted(instances, key=lambda i: estats.instance_activity(i), 
                  reverse=True)

def user_activity(users):
    return sorted(users, key=lambda u: estats.instance_activity(u), 
                  reverse=True)
                  
def comment_score(comments):
    return sorted(comments, key=lambda c: c.poll.tally.score, 
                  reverse=True)

def dict_value_sorter(dict):
    def _sort(items):
        return sorted(items, key=lambda i: dict.get(i))
    return _sort

def comment_id(comments):
    return sorted(comments, key=lambda c: c.id)


#
# Unadapted Ruby, either find a python lib with p distribution tables or 
# hardcode the "power" argument. 
#
#def wilson_confidence_interval(pos, n, power):
#    if n == 0:
#        return 0
#    
#    z = Statistics2.pnormaldist(1-power/2)
#    phat = 1.0*pos/n
#    (phat + z*z/(2*n) - z * Math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)