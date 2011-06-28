"""Handle URLs for the http://foursquare.com service. We are using
full blown oauth to access the user's details.
"""

from causal.main.decorators import can_view_service
from causal.main.models import UserService, RequestToken, ServiceApp, OAuth, AccessToken
from causal.main.utils.services import get_model_instance, user_login, \
     settings_redirect, check_is_service_id, get_url
from causal.main.utils.views import render
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect

PACKAGE = 'causal.foursquare'

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    """Handle the redirect from foursquare as part of the oauth process.
    """

    service = get_model_instance(request.user, PACKAGE)
    code = request.GET.get('code')

    url = "https://foursquare.com/oauth2/access_token?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=%s&code=%s" % (service.app.auth_settings['consumer_key'], service.app.auth_settings['consumer_secret'], service.app.auth_settings['return_url'], code)
    
    access_token = get_url(url)

    if access_token.has_key('error'):
        messages.error(request, 'Unable to validate your with Foursquare, please wait a few minutes and retry.')
    else:
        at = AccessToken.objects.create(
                oauth_token = access_token["access_token"],
                oauth_token_secret = '',
                oauth_verify = ''
            )
    
        service.auth.access_token = at
        service.auth.save()
        
        service.setup = True
        service.public = True
        service.save()
        
        
    return redirect(settings_redirect(request))

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """Setup oauth details for the return call from foursquare.
    """

    request.session['causal_foursquare_oauth_return_url'] = \
           request.GET.get('HTTP_REFERER', None)
    service = get_model_instance(request.user, PACKAGE)

    if not service.auth:
        auth_handler = OAuth()
        auth_handler.save()
        service.auth = auth_handler
        service.save()
        
    url = "https://foursquare.com/oauth2/authenticate?client_id=%s&response_type=code&redirect_uri=%s" % (service.app.auth_settings['consumer_key'], service.app.auth_settings['return_url'])
    
    return redirect(url)

@can_view_service
def stats(request, service_id):
    """Display stats based on checkins.
    """

    service = get_object_or_404(UserService, pk=service_id)

    if check_is_service_id(service, PACKAGE):
        template_values = {}
        # get checkins
        checkins = service.handler.get_items(date.today() - timedelta(days=7))

        template_values['checkins'] = checkins

        return render(
            request,
            template_values,
            'causal/foursquare/stats.html'
        )
    else:
        return redirect('/%s' % (request.user.username,))
