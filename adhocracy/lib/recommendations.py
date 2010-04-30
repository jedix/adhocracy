import math
import sys
import logging

from social import * 

log = logging.getLogger(__name__)

def log_with_null(n):
    return math.log(max(1,n))

def recommend(scope, user, count=5):
    dgb_pop_users = dict(delegateable_popular_agents(scope))
    usr_pop_users = dict(user_popular_agents(user))
    
    #log.debug("DGB POP DICT " + repr(dgb_pop_users))
    #log.debug("USR POP DICT " + repr(usr_pop_users))
        
    users = set(dgb_pop_users.keys() + usr_pop_users.keys())
    recs = dict()
    for u in users:
        if u == user or not u._has_permission('vote.cast'):
            continue
        recs[u] = (log_with_null(dgb_pop_users.get(u, 0)) * 2) + \
                  (usr_pop_users.get(u, 0) * 3)
    #log.debug("RECS DICT " + repr(recs))
    rs = sorted(recs.keys(), key=lambda u: recs[u], reverse=True)[0:count]
    #log.debug("RECS SORTING " + repr(rs))
    return rs