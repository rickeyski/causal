"""Deals with all the user accessable urls for http://facebook.com.
This service requires we use a facegraph python lib. Most of
the stats work is done using FQL."""

import cgi
from causal.facebook.service import get_items, get_stats_items
from causal.main.decorators import can_view_service
from causal.main.models import AccessToken, ServiceApp, UserService
from causal.main.service_utils import get_model_instance, get_module_name, \
     settings_redirect, check_is_service_id
from datetime import datetime, date, timedelta
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
import urllib

# Yay, let's recreate __package__ for Python <2.6
MODULE_NAME = get_module_name(__name__)

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    """Get the values back from facebook and store them for use later."""
    
    service = get_model_instance(request.user, MODULE_NAME)
    code = request.GET.get('code')
    callback = "%s%s" % (service.app.oauth.callback_url_base, 
                         reverse('causal-facebook-callback'),)
    url = "%s&code=%s&client_secret=%s&redirect_uri=%s&client_id=%s" % (
        service.app.oauth.access_token_url,
        code,
        service.app.oauth.consumer_secret,
        callback,
        service.app.oauth.consumer_key
    )
    
    response = cgi.parse_qs(urllib.urlopen(url).read())

    if response.has_key('access_token'):
        # Delete existing token
        AccessToken.objects.filter(service=service).delete()
        # Before creating a new one
        AccessToken.objects.create(
            service=service,
            oauth_token=''.join(response["access_token"]),
            oauth_token_secret='',
            created=datetime.now(),
            oauth_verify=''
        )
        service.setup = True
        service.public = True
        service.save()
        messages.success(request, 'Connection to Facebook complete.')
        
    else:
        messages.error(request, 'There was an error connnecting to Facebook.')

    return redirect(settings_redirect(request))

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """First leg of the two stage auth process. We setup and take note"""
    
    request.session['causal_facebook_oauth_return_url'] = \
        request.GET.get('HTTP_REFERER', None)
    service = get_model_instance(request.user, MODULE_NAME)

    if not service:
        app = ServiceApp.objects.get(module_name=MODULE_NAME)
        service = UserService(user=request.user, app=app)
        service.save()
    callback = "%s%s" % (service.app.oauth.callback_url_base, 
                         reverse('causal-facebook-callback'),)
    return redirect("%s&redirect_uri=%s&scope=%s&client_id=%s" % (
            service.app.oauth.request_token_url,
            callback,
            'read_stream,offline_access',
            service.app.oauth.consumer_key
        )
    )
        
@can_view_service
def stats(request, service_id):
    """Display stats based on checkins."""
    
    service = get_object_or_404(UserService, pk=service_id)
    
    if check_is_service_id(service, MODULE_NAME):
        return render_to_response(
            service.template_name + '/stats.html',
            {'statuses' : get_stats_items(request.user, date.today() - timedelta(days=7), 
                                    service)},
            context_instance=RequestContext(request)
        )
    else:
        return redirect('/%s' %(request.user.username))
