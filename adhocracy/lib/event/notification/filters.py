
def self_filter(pipeline):
    for notification in pipeline:
        if not notification.event.agent == notification.user: 
            yield notification
            
def duplicates_filter(pipeline):
    recipient_map = {}
    for notification in pipeline:
        highest = recipient_map.get(notification.user)
        if (not highest) or (highest.priority <= notification.priority):
            recipient_map[notification.user] = notification
    for notification in recipient_map.values(): yield notification