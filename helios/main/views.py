from time import mktime
from datetime import datetime, timedelta, date
import pretty

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.template import RequestContext
from django.utils import simplejson
from django.utils.html import urlize
import settings
from helios.main.forms import RegistrationForm
from helios.main.models import *

def history(request, user_id=None):
    template_values = {}

    if user_id:
        user = get_object_or_404(User, pk=user_id)
    else:
        if request.user.is_authenticated() and request.user.is_active:
            user = request.user
        else:
            return redirect('login')

    services = UserService.objects.filter(user=request.user)
    template_values['services'] = services

    days = []
    day_names = {}
    days_to_i = {}
    day_one = date.today() - timedelta(days=7)
    today = date.today()

    for i in range(0,7):
        last = today - timedelta(days=i)
        days.append([])
        day_names[i] = last.strftime('%A')
        days_to_i[day_names[i]] = i

    template_values['days'] = days
    template_values['day_names'] = day_names

    return render_to_response(
        'index.html',
        template_values,
        context_instance=RequestContext(request)
    )

def history_callback(request, service_id):
    template_values = {}
    service = get_object_or_404(UserService, pk=service_id)

    days = []
    days_to_i = {}
    day_one = date.today() - timedelta(days=7)
    today = date.today()

    for i in range(0,7):
        last = today - timedelta(days=i)
        days.append([])
        days_to_i[last.strftime('%A')] = i

    items = service.app.module.get_items(request.user, day_one, service)
    if items:
        for item in items:
            if item.created.date() > day_one:
                item_dict = {
                    'title': item.title,
                    'body': urlize(item.body),
                    'created': mktime(item.created.timetuple()),
                    'created_date': pretty.date(item.created),
                    'location': item.location,
                    'class_name' : item.class_name,
                    'has_location': item.has_location(),
                }
                days[days_to_i[item.created.strftime('%A')]].append(item_dict)

    response = {
        'class': service.class_name,
        'items': days,
    }
    return HttpResponse(simplejson.dumps(response))

def register(request):
    form = RegistrationForm()

    if request.user.is_authenticated():
        return redirect('/')

    if request.method == 'POST':

        form = RegistrationForm(request.POST)
        if form.is_valid():
            User.objects.create_user(form.cleaned_data['email'],
                form.cleaned_data['email'],
                form.cleaned_data['password1'])

            user = authenticate(username=form.cleaned_data['email'],
                                password=form.cleaned_data['password1'])
            login(request, user)

            return redirect('history')

    return render_to_response(
        'accounts/register.html',
        {
            'form' : form,
        },
        context_instance=RequestContext(request)
    )

@login_required(redirect_field_name='redirect_to')
def profile(request):
    """Edit access to various services"""
    available_services_oauth = []
    available_services_username = []
    enabled_services = []

    # need to diff between the services a user has signed up for 
    enabled_services_raw = request.user.userservice_set.all()
    
    for ser in enabled_services_raw:
        enabled_services.append(ser.class_name.replace('helios-', ''))
    
    for service in settings.INSTALLED_SERVICES:
        service = service.replace('helios.', '')
        if service not in enabled_services:
            if service in ('lastfm'):
                available_services_username.append(service)
            else:
                available_services_oauth.append(service)
    
    return render_to_response(
        'accounts/profile.html',
        {'available_services_oauth' : available_services_oauth,
         'available_services_username' : available_services_username,
         'enabled_services' : enabled_services,
        },
        context_instance=RequestContext(request)
    )

def index(request):
    if request.user.is_authenticated():
        return redirect('/history/')
    return render_to_response(
        'homepage.html',
        {
        },
        context_instance=RequestContext(request)
    )

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')