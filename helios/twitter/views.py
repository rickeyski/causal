from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from helios.main.models import UserService, RequestToken, OAuthSetting, ServiceApp
from helios.twitter.utils import user_login
from helios.main.service_utils import get_model_instance, generate_access_token, get_module_name
from helios.twitter.service import get_items
from datetime import date, timedelta
import re
from django.shortcuts import render_to_response
from django.template import RequestContext

# Yay, let's recreate __package__ for Python <2.6
MODULE_NAME = get_module_name(__name__)

@login_required(redirect_field_name='redirect_to')
def verify_auth(request):
    """Take incoming request and validate it to create a valid AccessToken."""
    service = get_model_instance(request.user, MODULE_NAME)
    request_token = RequestToken.objects.get(service=service)
    request_token.oauth_verify = request.GET.get('oauth_verifier')
    request_token.save()
    generate_access_token(service, request_token)
    return_url = request.session.get('helios_twitter_oauth_return_url', None) or 'history'
    # Mark as setup completed
    service.setup = True
    service.save()
    return redirect(return_url)

@login_required(redirect_field_name='redirect_to')
def auth(request):
    """Prepare a oauth request by saving a record locally ready for the
    redirect from twitter."""
    request.session['helios_twitter_oauth_return_url'] = request.GET.get('HTTP_REFERER', None)
    service = get_model_instance(request.user, MODULE_NAME)
    if not service:
        app = ServiceApp.objects.get(module_name=MODULE_NAME)
        service = UserService(user=request.user, app=app)
        service.save()
    return user_login(service)

@login_required(redirect_field_name='redirect_to')
def stats(request):
    """Take incoming request and validate it to create a valid AccessToken."""
    
    service = get_model_instance(request.user, MODULE_NAME)
    
    # get tweets
    tweets = get_items(request.user, date.today() - timedelta(days=7), service)
    retweets = 0
    template_values = {}
    
    # retweet ratio
    # who you tweet the most
    ats = {}
    if tweets:
        for tweet in tweets:
            if re.match('RT', tweet.body):
                retweets = retweets + 1
            atteds = re.findall('@[\w]*', tweet.body)
            for i in atteds:
                if ats.has_key(i):
                    ats[i] = ats[i] + 1
                else:
                    ats[i] = 1
            
        template_values['retweets'] = retweets
        template_values['non_retweets'] = len(tweets) - retweets
        template_values['total_tweets'] = len(tweets)
        template_values['atters'] = ats
        
    return render_to_response(
      'twitter_stats.html',
      template_values,
      context_instance=RequestContext(request)
    )

