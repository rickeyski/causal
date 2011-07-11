"""Handle account settings for flickr and other direct url requests."""

import httplib2
from oauth2 import Consumer, Token, Client
from causal.main.decorators import can_view_service
from causal.main.models import OAuth, RequestToken, AccessToken, UserService
from causal.main.utils.services import settings_redirect, get_model_instance, generate_access_token
from causal.main.utils.views import render
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

PACKAGE = 'causal.flickr'

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    """Take incoming request and validate it to create a valid AccessToken."""
    service = get_model_instance(request.user, PACKAGE)
    service.auth.request_token.oauth_verify = request.GET.get('oauth_verifier')
    service.auth.request_token.save()
    
    if not generate_access_token(service, service.app.auth_settings['access_token_url']):
        messages.error(
                        request,
                        'Unable to validate your username with Flickr, please check grant permission for gargoyle.me to access your photos.'
                    )
        return HttpResponseRedirect(settings_redirect(request))

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
    """Prepare a oauth request by saving a record locally ready for the
    redirect from twitter."""
    
    service = get_model_instance(request.user, PACKAGE)
    
    if not service.auth:
        auth_handler = OAuth()
    else:
        auth_handler = service.auth    
    
        
    current_site = Site.objects.get(id=settings.SITE_ID)
    callback = reverse('causal-flickr-callback')
    callback = "http://%s%s" % (current_site.domain, callback,)
    consumer = Consumer(service.app.auth_settings['consumer_key'], service.app.auth_settings['consumer_secret'])
    token = Token(service.app.auth_settings['consumer_key'], service.app.auth_settings['consumer_secret'])
    token.callback = callback
    client = Client(consumer)
    
    resp, content = client.request(service.app.auth_settings['request_token_url'], "POST", body='oauth_callback=%s' % (callback),
                                   headers={'Content-Type' :'application/x-www-form-urlencoded'})
    oauth_callback_confirmed, oauth_token, oauth_token_secret = content.split('&')
    
    new_rt = RequestToken()
    new_rt.oauth_token = oauth_token.split('=')[1]
    new_rt.oauth_token_secret = oauth_token_secret.split('=')[1]
    new_rt.save()
    
    auth_handler.request_token = new_rt
    auth_handler.save()
    if not service.auth:
        service.auth = auth_handler
        service.save()
    
    #http://www.flickr.com/services/oauth/authorize
    
    return redirect('http://www.flickr.com/services/oauth/authorize?oauth_token=%s&perms=read' %(oauth_token.split('=')[1]))

@can_view_service
def stats(request, service_id):
    """Create up some stats.
    """

    service = get_object_or_404(UserService, pk=service_id)

    if check_is_service_id(service, PACKAGE_NAME):
        pictures = service.handler.get_stats_items(date.today() - timedelta(days=7))
        template_values = {}
        # Most commented
        comments = 0
        template_values['most_commented_picture'] = None
        template_values['number_of_pictures_favorites'] = 0
        template_values['cameras_used'] = {}
        template_values['days_taken'] = generate_days_dict()
        
        number_of_pictures_favorites = 0

        for pic in pictures:
            if pic.has_location():
                template_values['pic_centre'] = pic

            if pic.favorite:
                template_values['number_of_pictures_favorites'] = \
                               number_of_pictures_favorites + 1

            if hasattr(pic, 'number_of_comments'):
                if int(pic.number_of_comments) > comments:
                    comments = pic.number_of_comments
                    template_values['most_commented_picture'] = pic

            # Get camera used count
            if template_values['cameras_used'].has_key(pic.camera_make + ' - ' + pic.camera_model):
                template_values['cameras_used'][pic.camera_make + ' - ' + pic.camera_model] = \
                               template_values['cameras_used'][pic.camera_make + ' - ' + pic.camera_model] + 1
            else:
                if hasattr(pic, 'camera_make'):
                    template_values['cameras_used'][pic.camera_make + ' - ' + pic.camera_model] = 1
                 
            if template_values['days_taken'].has_key(pic.created.date()):
                template_values['days_taken'][pic.created.date()] = \
                               template_values['days_taken'][pic.created.date()] + 1
                    
        template_values['cameras_used'] = SortedDict(sorted(template_values['cameras_used'].items(), reverse=True, key=lambda x: x[1]))
        template_values['pictures'] = pictures
        template_values['number_of_pictures_uploaded'] = len(pictures)
        template_values['days_taken'] = SortedDict(sorted(template_values['days_taken'].items(), reverse=False, key=lambda x: x[0]))
        
        max_taken_on_a_day = SortedDict(sorted(template_values['days_taken'].items(), reverse=True, key=lambda x: x[1]))
        template_values['max_taken_on_a_day'] = max_taken_on_a_day[max_taken_on_a_day.keyOrder[0]] + 1

        if template_values['number_of_pictures_favorites'] == 0:
            template_values['number_of_pictures_favorites'] = "No favourite pictures this week."

        return render(
            request,
            template_values,
            'causal/flickr/stats.html'
        )
    else:
        return redirect('/%s' %(request.user.username,))
