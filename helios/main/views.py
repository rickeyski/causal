from datetime import datetime, timedelta, date

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.template import RequestContext

from helios.main.forms import RegistrationForm
from helios.main.models import *

@login_required(redirect_field_name='redirect_to')
def history(request):
    template_values = {}

    if request.method == 'GET':
        services = Service.objects.filter(user=request.user)
        template_values['services'] = services

        days = []
        day_names = {}
        days_to_i = {}
        day_one = date.today() - timedelta(days=7)

        for i in range(0,7):
            today = date.today()
            last = today - timedelta(days=i)
            days.append([])
            day_names[i] = last.strftime('%A')
            days_to_i[day_names[i]] = i

        for service in services:
            app = service.app
            items = app.utils.get_items(user=request.user)
            for item in items:
                if item.created.date > day_one:
                    days[days_to_i[item.created.strftime('%A')]].append(item)

        if days:
            for day in days:
                day.sort(key=lambda item:item.created.date, reverse=True)
            template_values['days'] = days

        template_values['days'] = days
        template_values['day_names'] = day_names

    return render_to_response(
        'index.html',
        template_values,
        context_instance=RequestContext(request)
    )

@login_required(redirect_field_name='redirect_to')
def oauth_login(request, service=None):

    if request.method == 'GET':
        oauth_details = OAUTH_APP_SETTINGS[service]
        consumer = oauth.Consumer(OAUTH_APP_SETTINGS[service]['consumer_key'],
                                  OAUTH_APP_SETTINGS[service]['consumer_secret'])

        client = oauth.Client(consumer)
        resp, content = client.request(oauth_details['request_token_url'], "GET")

        if resp['status'] != '200':
            print "fail"

        request_token_params = dict((token.split('=') for token in content.split('&')))

        token = OAuthRequestToken()
        token.service=service
        token.user = request.user
        token.oauth_token = request_token_params['oauth_token']
        token.oauth_token_secret = request_token_params['oauth_token_secret']
        token.created = datetime.now()
        token.save()

    return HttpResponseRedirect("%s?oauth_token=%s" % (oauth_details['user_auth_url'],
                                         request_token_params['oauth_token']))

def oauth_callback(request, service=None):
    consumer = oauth.Consumer(OAUTH_APP_SETTINGS[service]['consumer_key'],
                                  OAUTH_APP_SETTINGS[service]['consumer_secret'])

    params = {
        'oauth_token' : request.GET['oauth_token'],
        'service' : service,
        }

    request_token = OAuthRequestToken.objects.filter(**params)[0]

    token = oauth.Token(request_token.oauth_token, request_token.oauth_token_secret)
    client = oauth.Client(consumer, token)
    resp, content = client.request(OAUTH_APP_SETTINGS[service]['access_token_url'], "POST")

    access_token = dict((token.split('=') for token in content.split('&')))

    token_save = OAuthAccessToken()
    token_save.service=service
    token_save.user=request.user
    token_save.create=datetime.now()
    token_save.oauth_token=access_token['oauth_token']
    token_save.oauth_token_secret=access_token['oauth_token_secret']

    token_save.save()

    return HttpResponseRedirect('/history/')

def register(request):
    form = RegistrationForm()

    if request.user.is_authenticated():
        return HttpResponseRedirect('/history/')

    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():
            User.objects.create_user(form.cleaned_data['email'],
                form.cleaned_data['email'],
                form.cleaned_data['password1'])

            user = authenticate(username=form.cleaned_data['email'],
                                password=form.cleaned_data['password1'])
            login(request, user)

            return HttpResponseRedirect('/history/')

    return render_to_response('accounts/register.html',{
        'form' : form,
        },
        context_instance=RequestContext(request))

@login_required(redirect_field_name='redirect_to')
def profile(request):
    form = LastFMSettingsForm()
    twitter = None
    foursquare = None
    lastfm = None

    if request.POST:
        form = LastFMSettingsForm(request.POST)
        if form.is_valid():
            last = LastFMSettings()
            last.user = request.user
            last.username = form.cleaned_data['username']
            last.save()

    tokens = request.user.oauthaccesstoken_set.all()
    for token in tokens:
        if token.service == 'twitter':
            twitter = True
        if token.service == 'foursquare':
            foursquare = True

    return render_to_response('accounts/profile.html',{
        'form' : form,
        'twitter' : twitter,
        'foursquare' : foursquare,
        },
        context_instance=RequestContext(request))
