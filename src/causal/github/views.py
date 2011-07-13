""" Handler for URLs for the http://github.com service.
GitHub doesn't really have a decent oauth service so again we
are hitting public json feeds and processing those.
"""

from datetime import datetime
import httplib2
from causal.main.decorators import can_view_service
from causal.main.models import OAuth, RequestToken, AccessToken, UserService
from causal.main.utils.services import get_model_instance, \
        settings_redirect, check_is_service_id, get_data, get_url
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

    try:
        service = get_model_instance(request.user, PACKAGE)
        code = request.GET.get('code')
    
        if code:
            # swap our newly aquired code for a everlasting signed "token"
            h = httplib2.Http()
            resp, content = h.request('https://github.com/login/oauth/access_token?client_id=%s&client_secret=%s&code=%s' % (
                service.app.auth_settings['consumer_key'], 
                service.app.auth_settings['consumer_secret'], 
                code), 
                "POST")
        
            if not resp['status'] == '200' or not content.startswith('access_token'):
                raise Exception('Token Failure')
            
            access, perm_type = content.split('&')
            # go and fetch the login for the github user
            user_json = get_url('https://api.github.com/user?access_token=%s' %(access.split('=')[1]))
            
            if user_json.has_key('login'):
                at = AccessToken.objects.create(
                    oauth_token = access.split('=')[1],
                    oauth_token_secret = access.split('=')[1],
                )
                
                service.auth.access_token = at
                service.auth.save()
                
                ## Mark as setup completed
                service.setup = True    
                service.save()
    except:
        messages.error(
            request,
            'Unable to validate your account with GitHub, please check grant permission for gargoyle.me to access your photos.'
        )

    return redirect(settings_redirect(request))

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """We dont need a full oauth setup just a username.
    """

    service = get_model_instance(request.user, PACKAGE)
    
    if not service.auth:
        auth = OAuth()
        auth.save()
        service.auth = auth
        service.save()
        
    current_site = Site.objects.get(id=settings.SITE_ID)
    callback = reverse('causal-github-callback')
    callback = "http://%s%s" % (current_site.domain, callback,)

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
