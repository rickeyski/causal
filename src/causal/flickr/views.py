"""Handle account settings for flickr and other direct url requests."""

import httplib2
from causal.main.decorators import can_view_service
from causal.main.models import UserService, Auth
from causal.main.utils.services import settings_redirect, OAuthClient
from causal.main.utils.views import render
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import simplejson
from django.utils.datastructures import SortedDict

PACKAGE = 'causal.flickr'

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    pass

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """Prepare a oauth request by saving a record locally ready for the
    redirect from twitter."""
    
    request.session['causal_flickr_oauth_return_url'] = \
           request.GET.get('HTTP_REFERER', None)
    service = get_model_instance(request.user, PACKAGE)
    return user_login(service)

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
