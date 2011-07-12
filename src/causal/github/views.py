""" Handler for URLs for the http://github.com service.
GitHub doesn't really have a decent oauth service so again we
are hitting public json feeds and processing those.
"""

from datetime import datetime
import httplib2
from causal.main.decorators import can_view_service
from causal.main.models import OAuth, RequestToken, AccessToken, UserService
from causal.main.utils.services import get_model_instance, \
        settings_redirect, check_is_service_id, get_data
from causal.main.utils.views import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from datetime import date, timedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

PACKAGE = 'causal.github'

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    """Handle reply from github"""
    """Take incoming request and validate it to create a valid AccessToken."""

    service = get_model_instance(request.user, PACKAGE)
    code = request.GET.get('code')
    if not code:
        messages.error(
                    request,
                    'Unable to validate your account with GitHub, please check grant permission for gargoyle.me to access your photos.'
                )

    h = httplib2.Http()
    resp, content = h.request('https://github.com/login/oauth/access_token?client_id=%s&client_secret=%s&code=%s' % (
        service.app.auth_settings['consumer_key'], 
        service.app.auth_settings['consumer_secret'], 
        code), 
        "POST")

    access, perm_type = content.split('&')
    
    at = AccessToken.objects.create(
        oauth_token = access.split('=')[1],
        oauth_token_secret = access.split('=')[1],
    )
    
    ## Mark as setup completed
    service.setup = True

    ## Test if service is protected on twitter's side
    ## if so mark it
    #twitter_user = get_user(service)
    #if twitter_user.protected:
        #service.public = False
    #else:
        #service.public = True

    service.save()

    return redirect(settings_redirect(request))

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """We dont need a full oauth setup just a username.
    """

    service = get_model_instance(request.user, PACKAGE)
    if not service.auth:
        auth_handler = OAuth()
    else:
        auth_handler = service.auth    
    
        
    current_site = Site.objects.get(id=settings.SITE_ID)
    callback = reverse('causal-github-callback')
    callback = "http://%s%s" % (current_site.domain, callback,)
    #consumer = Consumer(service.app.auth_settings['consumer_key'], service.app.auth_settings['consumer_secret'])
    #client = Client(consumer)

    #resp, content = client.request(service.app.auth_settings['request_token_url'], "POST", body='oauth_callback=%s' % (callback),
                                   #headers={'Content-Type' :'application/x-www-form-urlencoded'})
    
    #oauth_callback_confirmed, oauth_token, oauth_token_secret = content.split('&')
    
    #new_rt = RequestToken()
    #new_rt.oauth_token = oauth_token.split('=')[1]
    #new_rt.oauth_token_secret = oauth_token_secret.split('=')[1]
    #new_rt.save()
    
    #auth_handler.request_token = new_rt
    #auth_handler.save()
    #if not service.auth:
        #service.auth = auth_handlerservice.app.auth_settings['consumer_key']
        #service.save()
    
    return redirect('https://github.com/login/oauth/authorize?client_id=%s&redirect_uri=%s' %(
        service.app.auth_settings['consumer_key'],
        callback
    ))

@can_view_service
def stats(request, service_id):
    """Create up some stats.
    """

    service = get_object_or_404(UserService, pk=service_id)

    if check_is_service_id(service, PACKAGE):
        commits, avatar, commit_times, common_time, days_committed, max_commits_on_a_day = service.handler.get_stats_items(date.today() - timedelta(days=7))

        return render(
            request,
            {
                'commits': commits,
                'avatar' : avatar,
                'commit_times' : commit_times,
                'common_time' : common_time,
                'days_committed' : days_committed, 
                'max_commits_on_a_day' : max_commits_on_a_day
            },
            'causal/github/stats.html'
        )
    else:
        return redirect('/%s' % (request.user.username,))
