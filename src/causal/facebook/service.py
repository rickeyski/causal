"""Communicate with Facebook and fetch various updates.
We use FQL to fetch results from Facebook.
"""

from causal.main.exceptions import LoggedServiceError
from causal.main.models import ServiceItem, AccessToken
from causal.main.service_utils import get_model_instance
from datetime import datetime
from django.shortcuts import redirect
from facegraph.fql import FQL
import time

DISPLAY_NAME = 'Facebook'
CUSTOM_FORM = False
OAUTH_FORM = True

# fetch all statuses for a user
STATUS_FQL = """SELECT uid,status_id,message,time FROM status WHERE uid = me() AND time > %s"""

# links posted
LINKED_FQL = """SELECT owner_comment,created_time,title,summary,url FROM link WHERE owner=me() AND created_time > %s"""

# users stream needs fixing
STREAM_FQL = """SELECT likes,message,created_time,comments,permalink,privacy,source_id FROM stream WHERE filter_key IN (SELECT filter_key FROM stream_filter WHERE uid = me() AND type="newsfeed") AND created_time > %s"""

# fetch username
USER_NAME_FETCH = """SELECT name, pic_small FROM user WHERE uid=%s"""

# fetch uid
USER_ID = """SELECT uid FROM user WHERE uid = me()"""

def enable():
    """Setup and authorise the service."""
    return redirect('causal-facebook-auth')

def get_items(user, since, model_instance=None):
    """Fetch main stats for history page."""
    
    serv = model_instance or get_model_instance(user, __name__)
    access_token = AccessToken.objects.get(service=serv)

    try:
        query = FQL(access_token.oauth_token)
        uid_result = query(USER_ID)
        if uid_result:
            uid = uid_result[0]['uid']
        week_ago_epoch = time.mktime(since.timetuple())
        status_stream = _fetch_feed(STATUS_FQL % int(week_ago_epoch))
            
    except Exception, exception:
        raise LoggedServiceError(original_exception=exception)

    if getattr(status_stream, 'error_code', False):
        raise LoggedServiceError(
        'Facebook service failed to fetch items for causal-user %s, error: %s' % \
            (user.username, status_stream['error_msg'])
        )
    
    return _convert_status_feed(serv, user, status_stream, uid, since)

def get_stats_items(user, since, model_instance=None):
    """Return more detailed ServiceItems for the stats page."""
    
    serv = model_instance or get_model_instance(user, __name__)
    access_token = AccessToken.objects.get(service=serv)
    week_ago_epoch = time.mktime(since.timetuple())
    
    query = FQL(access_token.oauth_token)
    uid_result = query(USER_ID)
    if uid_result:
        uid = uid_result[0]['uid']    
    
    # get links posted
    try:
        link_stream = _fetch_feed(serv, access_token, LINKED_FQL % int(week_ago_epoch))
    except Exception, exception:
        return LoggedServiceError(original_exception=exception)

    if link_stream:
        links = _convert_link_feed(serv, user, link_stream, since)
    
    # get statuses
    try:
        status_stream = _fetch_feed(serv, access_token, STATUS_FQL % int(week_ago_epoch))
    except Exception, exception:
        return LoggedServiceError(original_exception=exception)
            
    if status_stream:
        statuses = _convert_status_feed(serv, user, status_stream, uid, since)
    
    # details stats:
    try:
        stream_stream = _fetch_feed(serv, access_token, STREAM_FQL % int(week_ago_epoch))
    except Exception, exception:
        return LoggedServiceError(original_exception=exception)
    items = []
    for strm in stream_stream:
        # do we have permission from the user to post entry?
        # ignore if the post is entry
        if strm['comments']['can_post'] and strm.has_key('message'):
            if strm.has_key('likes') and strm['likes'].has_key('user_likes'):
                if strm['likes']['user_likes']:
                    item = ServiceItem()
                    item.liked = strm['likes']['user_likes']
                    item.who_else_liked = strm['likes']['href']
                    item.created = datetime.fromtimestamp(strm.created_time)
                    item.body = strm.message
                    
                    # go off and fetch details about a user
                    item.other_peoples_comments = []
                    for comment in strm['comments']['comment_list']:
                        users = q(USER_NAME_FETCH % comment['fromid'])
                        for user in users:
                            user_details = {
                                'name' : user['name'],
                                'profile_pic' : user['pic_small']
                            }
                            item.other_peoples_comments.append(user_details)
                    item.service = serv
                    item.user = user
                    item.link_back = strm['permalink']
                    items.append(item)
    # get pics in which they are tagged
    
    # get pics posted
    
    # get places visited
    
    return links, statuses, items

def _fetch_feed(serv, access_token, fql):
    """Generic method to fetch FQL from Facebook."""
    
    query = FQL(access_token.oauth_token)
    status_stream = query(fql)
        
    return status_stream

def _convert_link_feed(serv, user, stream, since):
    """Convert link feed."""
    
    items = []
    
    for entry in stream:
        if entry.has_key('created_time'):
            created = datetime.fromtimestamp(entry['created_time'])
            
            if created.date() >= since:
                item = ServiceItem()
                item.created = datetime.fromtimestamp(entry.created_time)
                item.link_back = entry.url
                item.title = entry.title
                item.body = entry.summary
                item.url = entry.url
                item.service = serv
                item.user = user
                items.append(item)
    
    return items

def _convert_status_feed(serv, user, user_stream, uid, since):
    """Take the feed of status updates from facebook and convert it to 
    ServiceItems."""

    items = []
    
    for entry in user_stream:
        if entry.has_key('message'):
            created = datetime.fromtimestamp(entry['time'])
            
            if created.date() >= since:
                item = ServiceItem()
                item.created = datetime.fromtimestamp(entry['time'])
                item.title = ''
                item.body = entry['message']
                item.link_back = \
                    "http://www.facebook.com/%s/posts/%s?notif_t=feed_comment" % (uid, entry['status_id'])
                item.service = serv
                item.user = user
                item.created = created
                items.append(item)

    return items