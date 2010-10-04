from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from causal.main.models import UserService, RequestToken, OAuthSetting, ServiceApp
from causal.main.service_utils import get_model_instance, user_login, generate_access_token, get_module_name
from causal.foursquare.service import get_items
from datetime import date, timedelta
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

# Yay, let's recreate __package__ for Python <2.6
MODULE_NAME = get_module_name(__name__)

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    service = get_model_instance(request.user, MODULE_NAME)
    request_token = RequestToken.objects.get(service=service)
    request_token.oauth_verify = request.GET.get('oauth_verifier')
    request_token.save()
    return_url = request.session.get('causal_foursquare_oauth_return_url', None) or 'history'
    generate_access_token(service, request_token)
    service.setup = True
    service.save()
    return redirect(return_url)

@login_required(redirect_field_name='redirect_to')
def auth(request):
    request.session['causal_foursquare_oauth_return_url'] = request.GET.get('HTTP_REFERER', None)
    service = get_model_instance(request.user, MODULE_NAME)
    if not service:
        app = ServiceApp.objects.get(module_name=MODULE_NAME)
        service = UserService(user=request.user, app=app)
        service.save()
    return user_login(service)

def stats(request, service_id):
    """Display stats based on checkins."""
    service = get_object_or_404(UserService, pk=service_id)
    template_values = {}
    # get checkins
    checkins = get_items(request.user, date.today() - timedelta(days=7), service)
    template_values['checkins'] = checkins
    return render_to_response(
      service.app.module_name + '/stats.html',
      template_values,
      context_instance=RequestContext(request)
    )