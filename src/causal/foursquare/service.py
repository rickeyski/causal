import httplib2
import oauth2 as oauth
from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import render_to_response, redirect
from django.conf import settings
from causal.main.handlers import OAuthServiceHandler
from causal.main.models import ServiceItem
from causal.main.utils.services import get_model_instance, get_data, get_url
from causal.main.exceptions import LoggedServiceError

ENABLE_PERSONAL_DATA_STORE = getattr(settings, 'ENABLE_PERSONAL_DATA_STORE', False)

class ServiceHandler(OAuthServiceHandler):
    display_name = 'Foursquare'

    def get_items(self, since):
        """Fetch the history of checkins for the current user.
        """

        try:
            url = "https://api.foursquare.com/v2/users/self/checkins?oauth_token=%s" % (self.service.auth.access_token.oauth_token)
            checkins = get_url(url)
        except Exception, e:
            messages.error(request, "Unable to to contact Foursquare's servers, please wait a few minutes and retry or check http://status.foursquare.com.")
            raise LoggedServiceError(original_exception=e)

        return self._convert_feed(checkins, since)

    def _convert_feed(self, json, since):
        """Take the raw json from the feed and convert it to ServiceItems.
        """

        items = []
        if json and json['response'].has_key('checkins'):
            for checkin in json['response']['checkins']['items']:
                created = datetime.fromtimestamp(checkin['createdAt'])

                if created.date() >= since:
                    item = ServiceItem()
                    item.link_back = 'http://foursquare.com/venue/%s' % (checkin['venue']['id'],)
                    item.title = checkin['venue']['name']

                    if checkin.has_key('shout') and checkin['shout']:
                        item.body = checkin['shout']
                    else:
                        if len(checkin['venue']['categories']) > 0 and checkin['venue']['location'].has_key('city'):
                            item.body = "A %s in %s" % (checkin['venue']['categories'][0]['name'], checkin['venue']['location']['city'])
                        elif checkin['venue'].has_key('city'):
                            item.body = "In %s" % (checkin['venue']['location']['city'])
                        else:
                            item.body = "%s" % (checkin['venue']['name'])

                    if checkin['venue']['location'].has_key('lat') and checkin['venue']['location']['lng']:
                        item.location['lat'] = checkin['venue']['location']['lat']
                        item.location['long'] = checkin['venue']['location']['lng']

                    item.created = created
                    item.service = self.service

                    if checkin.has_key('isMayor'):
                        item.is_mayor = checkin['isMayor']
                    else:
                        pass

                    if checkin['venue'].has_key('categories') and len(checkin['venue']['categories']) > 0:
                        item.icon = checkin['venue']['categories'][0]['icon']

                    if ENABLE_PERSONAL_DATA_STORE:
                        item.external_service_id = checkin['id']
                    items.append(item)
        return items
