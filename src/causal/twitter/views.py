"""Handles user accessable urls for http://twitter.com service.
We ask for read only permissions using full blown oauth2.
"""

import re
import logging
import tweepy
from causal.main.decorators import can_view_service
from causal.main.models import UserService, RequestToken
from causal.main.utils.services import get_model_instance, \
     generate_access_token, settings_redirect, check_is_service_id, generate_days_dict
from causal.main.utils.views import render
from causal.twitter.utils import _oauth, user_login, get_user
from datetime import date, timedelta
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.datastructures import SortedDict

PACKAGE = 'causal.twitter'

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    """Take incoming request and validate it to create a valid AccessToken."""
    service = get_model_instance(request.user, PACKAGE)
    service.auth.request_token.oauth_verify = request.GET.get('oauth_verifier')
    service.auth.request_token.save()
    
    if not generate_access_token(service, "https://twitter.com/oauth/access_token"):
        messages.error(
                        request,
                        'Unable to validate your username with Flickr, please check your username and retry.'
                    )
        return HttpResponseRedirect(settings_redirect(request))

    # Mark as setup completed
    service.setup = True

    # Test if service is protected on twitter's side
    # if so mark it
    twitter_user = get_user(service)
    if twitter_user.protected:
        service.public = False
    else:
        service.public = True

    service.save()

    return HttpResponseRedirect(settings_redirect(request))

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """Prepare a oauth request by saving a record locally ready for the
    redirect from twitter."""
    request.session['causal_twitter_oauth_return_url'] = \
           request.GET.get('HTTP_REFERER', None)
    service = get_model_instance(request.user, PACKAGE)
    return user_login(service)

@can_view_service
def stats(request, service_id):
    """Create up some stats."""
    
    service = get_object_or_404(UserService, pk=service_id)

    if check_is_service_id(service, PACKAGE):
        # get tweets
        tweets = service.handler.get_items(date.today() - timedelta(days=7))
        retweets = 0
        template_values = {}

        # retweet ratio
        # who you tweet the most
        ats = {}
        
        template_values['days_tweeted'] = generate_days_dict()
            
        if tweets:
            for tweet in tweets:
                if tweet.has_location():
                    template_values['tweet_centre'] = tweet
                if re.match('RT', tweet.body):
                    retweets = retweets + 1
                else:
                    atteds = re.findall('@[\w]*', tweet.body)
                    for user in atteds:
                        username = user.split('@')[1]
                        if username:
                            if ats.has_key(user):
                                ats[user]['count'] += 1
                            else:
                                ats[user] = {'avatar': 'http://api.twitter.com/1/users/profile_image/%s.json' % (username),
                                          'count' : 1
                                }
    
                if template_values['days_tweeted'].has_key(tweet.created.date()):
                    template_values['days_tweeted'][tweet.created.date()] = \
                               template_values['days_tweeted'][tweet.created.date()] + 1

            template_values['retweets'] = retweets
            template_values['non_retweets'] = len(tweets) - retweets
            template_values['total_tweets'] = len(tweets)
            template_values['tweets'] = tweets

            # order by value and reverse to put most popular at the top
            template_values['atters'] = SortedDict(
                sorted(ats.items(), reverse=True, key=lambda x: x[1]['count']))
            
            template_values['days_tweeted'] = SortedDict(sorted(template_values['days_tweeted'].items(), reverse=False, key=lambda x: x[0]))
            
            max_tweeted_on_a_day = SortedDict(sorted(template_values['days_tweeted'].items(), reverse=True, key=lambda x: x[1]))
            template_values['max_tweeted_on_a_day'] = max_tweeted_on_a_day[max_tweeted_on_a_day.keyOrder[0]] + 1
            
        return render(
            request,
            template_values,
            'causal/twitter/stats.html'
        )
    else:
        return redirect('/%s' %(request.user.username))
