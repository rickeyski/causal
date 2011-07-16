import time
import feedparser
from dateutil import parser
from datetime import datetime, timedelta, date
from BeautifulSoup import Tag, SoupStrainer, BeautifulSoup as soup
from causal.main.handlers import OAuthServiceHandler
from causal.main.models import OAuth, RequestToken, AccessToken, UserService, ServiceItem
from causal.main.utils.services import get_model_instance, get_data, get_url, generate_days_dict
from causal.main.exceptions import LoggedServiceError
from django.utils.datastructures import SortedDict

KEEP_TAGS = ('a', 'span', 'code',)

class ServiceHandler(OAuthServiceHandler):
    display_name = 'Github'

    def get_items(self, since):
        """Fetch updates.
        """

        return self._convert_feed(
            self._get_feed(),
            since
        )

    def get_stats_items(self, since):
        """Fetch stats updates.
        """

        feed = self._get_feed()
        repos = self._get_repos(since)
        
        if not feed and not repo:
            return
        
        return self._convert_stats_feed(feed, since), repos
    
    
    def _get_feed(self):
        """Get the user's latest updates from github's json feed"""
        
        feed = None
        username = self._get_username()

        # check we have the username to access the json feed from github
        if username:
            feed = get_data(
                self.service,
                'https://github.com/%s.json' % (username),
                disable_oauth=True
            )
            
        return feed

    def _get_repos(self, since):
        """Fetch the repo list for a user."""
        
        repos_url = "https://api.github.com/user/repos?access_token=%s" % (self.service.auth.access_token.oauth_token)
        repos = get_url(repos_url)
        
        updated_repos = []
        for repo in repos:
            pushed = datetime.strptime(repo['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
            if pushed.date() > since:
                updated_repos.append(repo)
                
        return updated_repos
    
    def _convert_feed(self, feed, since):
        """Take the user's atom feed.
        """
        
        items = []

        for entry in feed:
            if entry.has_key('public') and entry['public']:
                created = self._convert_date(entry)

                if created.date() >= since:
                    item = ServiceItem()
                    self._set_title_body(entry, item)
                    item.created = created
                    if entry['type'] == 'GistEvent':
                        item.link_back = entry['payload']['url']
                    else:
                        if entry.has_key('url'):
                            item.link_back = entry['url']
                    item.service = self.service
                    items.append(item)

        return items

    def _convert_date(self, entry):
        """Apply the offset from github timing to the date.
        """

        converted_date = None

        if entry and entry.has_key('created_at'):

            date, time, offset = entry['created_at'].rsplit(' ')

            offset = offset[1:]
            offset = offset[:2]
            time_offset = timedelta(hours=int(offset))

            try:
                converted_date = datetime.strptime(date + ' ' + time, '%Y/%m/%d %H:%M:%S') + time_offset
            except:
                converted_date = datetime.now() + time_offset

        return converted_date

    def _convert_commit_date(self, commit):
        """Convert the date given in a commit api call."""
        
        if commit and commit.has_key('author') and commit['author'].has_key('date'):
            
            date, time_and_offset = commit['author']['date'].rsplit('T')
            time, offset = time_and_offset.rsplit('-')

            time_offset = timedelta(hours=int(offset[:2]))

            return datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M:%S') + time_offset

    def _convert_stats_feed(self, feed, since):
        """Take the user's atom feed.
        """

        items = []
        avatar = ""

        if feed and feed[0]['actor_attributes'].has_key('gravatar_id'):
            avatar = 'http://www.gravatar.com/avatar/%s' % (feed[0]['actor_attributes']['gravatar_id'],)

        commit_times = {}
        
        days_committed = generate_days_dict()
        username = self._get_username()
        
        for entry in feed:
            if entry['public']:
                dated, time, offset = entry['created_at'].rsplit(' ')
                created = self._convert_date(entry)

                if created.date() >= since:

                    # extract commits from push event
                    if entry['type'] == 'PushEvent':
                        
                        # fetch and get the stats on commits
                        for commit in entry['payload']['shas']:
                            
                            url = "https://api.github.com/repos/%s/%s/git/commits/%s?access_token=%s" % (
                                entry['repository']['owner'],
                                entry['repository']['name'], 
                                commit[0], 
                                self.service.auth.access_token.oauth_token)
                            commit_detail = get_data(self.service, url, disable_oauth=True)
                            #if commit_detail.has_key('message') and commit_detail['message'] == 'Not Found':
                            #    break
                            item = ServiceItem()
                            item.title = "Commit for %s" % (entry['repository']['name'])
                            item.body = '"%s"' % (commit_detail['message']) 
                            item.created = self._convert_commit_date(commit_detail)
                            
                            if commit_detail.has_key('url'):
                                item.link_back = commit_detail['url']

                            item.service = self.service
                            items.append(item)
                            
                            if days_committed.has_key(item.created.date()):
                                days_committed[item.created.date()] = days_committed[item.created.date()] + 1
                        
                            hour = created.strftime('%H')
                            if commit_times.has_key(hour):
                                commit_times[hour] += + 1
                            else:
                                commit_times[hour] = 1
                    else:
                        item = ServiceItem()
                        self._set_title_body(entry, item)
                        item.created = created
                        if entry.has_key('url'):
                            item.link_back = entry['url']
                        item.service = self.service
                        items.append(item)

        commit_times = SortedDict(sorted(
            commit_times.items(),
            reverse=True,
            key=lambda x: x[1]
        ))
        
        days_committed = SortedDict(sorted(days_committed.items(), reverse=False, key=lambda x: x[0]))
        max_commits_on_a_day = SortedDict(sorted(days_committed.items(), reverse=True, key=lambda x: x[1]))
        max_commits_on_a_day = max_commits_on_a_day[max_commits_on_a_day.keyOrder[0]] + 1

        return items, avatar, commit_times, self._most_common_commit_time(commit_times), days_committed, max_commits_on_a_day
    
    def _most_common_commit_time(self, commits):
        """Take a list of commit times and return the most common time
        of commits."""
        
        if not commits:
            return False
        
        hour = commits.keys()[0]
        
        if hour == '23':
            return '%s:00 and 00:00' % (hour)
        else:
            return '%s:00 and %s:00' % (hour, int(hour) + 1)
    
    def _set_title_body(self, entry, item):
        """Set the title and body based on the event type."""

        item.body = ''
        
        try:
            if entry['type'] == 'CreateEvent':
                if entry['payload'].has_key('object_name'):
                    item.title = "Created branch %s from %s" % (entry['payload']['object_name'], entry['payload']['name'])
                else:
                    item.title = "Created branch %s from %s" % (entry['payload']['master_branch'], entry['repository']['name'])                
            elif entry['type'] == 'GistEvent':
                item.title = "Created gist %s" % (entry['payload']['desc'])
            elif entry['type'] == 'IssuesEvent':
                item.title = "Issue #%s was %s." % (str(entry['payload']['number']), entry['payload']['action'])
            elif entry['type'] == 'ForkEvent':
                item.title = "Repo %s forked." % (entry['repository']['name'])
            elif entry['type'] == 'PushEvent':
                item.title = "Pushed to repo %s with comment \"%s\"." % (entry['repository']['name'], entry['payload']['shas'][0][2])
            elif entry['type'] == 'CreateEvent':
                item.title = "Branch %s for %s." % (entry['payload']['object_name'], entry['payload']['name'])
            elif entry['type'] == 'WatchEvent':
                item.title = "Started watching %s." % (entry['repository']['name'])
            elif entry['type'] == 'FollowEvent':
                item.title = "Started following %s." % (entry['payload']['target']['login'])
            elif entry['type'] == 'GistEvent':
                item.title = "Snippet: %s" % (entry['payload']['snippet'])
            elif entry['type'] == 'DeleteEvent':
                item.title = "Deleted: %s called %s" % (entry['payload']['ref_type'], entry['payload']['ref'])
            elif entry['type'] == 'GollumEvent':
                pass
            elif entry['type'] == 'IssueCommentEvent':
                item.title = "Commented on issue with id of %s" % (entry['payload']['issue_id'])
            elif entry['type'] == 'PullRequestEvent':
                item.title = "Created pull for %s" % (entry['repository']['name'])
            else:
                item.title = "Unknown Event!"
                
        except:
            item.title = "Unknown Event!"
            
    def _get_username(self):
        """Get a user's profile data"""
        
        user_json = get_url('https://api.github.com/user?access_token=%s' % (self.service.auth.access_token.oauth_token))
        
        if user_json.has_key('login'):
            return user_json['login']