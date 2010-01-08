import logging 

import webhelpers.text as text

from ... import mail
from ... import microblog

TWITTER_LENGTH = 140
TRUNCATE_EXT = '... '

log = logging.getLogger(__name__)

def log_sink(pipeline):
    for notification in pipeline:
        log.debug("Generated notification: %s" % notification)
        yield notification

def twitter_sink(pipeline):
    for notification in pipeline:
        user = notification.user
        if user.twitter and (notification.priority >= user.twitter.priority):
            notification.language_context()
            short_url = microblog.shorten_url(notification.link)
            remaining_length = TWITTER_LENGTH - \
                            (len(short_url) + len(TRUNCATE_EXT))
            tweet = text.truncate(notification.subject, remaining_length, 
                                  TRUNCATE_EXT, False)
            tweet += short_url
            try:
                api = microblog.create_api()
                api.PostDirectMessage(user.twitter.screen_name, tweet)
            except Exception, e:
                log.exception(e)
                yield notification
        else:
            yield notification

def mail_sink(pipeline):
    for notification in pipeline:
        if notification.priority >= notification.user.email_priority:
            notification.language_context() 
            headers = {'X-Notification-Id': notification.id,
                       'X-Notification-Priority': str(notification.priority)}
            try:
                mail.to_user(notification.user, 
                         notification.subject, 
                         notification.body, 
                         headers=headers)
            except Exception, e:
                log.exception(e)
                yield notification
        else:
            yield notification