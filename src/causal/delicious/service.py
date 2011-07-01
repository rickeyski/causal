"""This file provides the fetching and converting of the
feed from delicious.com.
"""

from dateutil import parser
from datetime import datetime, timedelta
from django.shortcuts import render_to_response, redirect
from django.utils import simplejson
from django.conf import settings
from causal.main.handlers import BaseServiceHandler
from causal.main.models import ServiceItem
from causal.main.utils.services import get_data
from causal.main.exceptions import LoggedServiceError

try:
    import hashlib
    hash = hashlib.md5()
except ImportError:
    # for Python < 2.5
    import md5
    hash = md5.new()

ENABLE_PERSONAL_DATA_STORE = getattr(settings, 'ENABLE_PERSONAL_DATA_STORE', False)

class ServiceHandler(BaseServiceHandler):
    display_name = 'Delicious'

    def get_items(self, since):
        url = 'http://feeds.delicious.com/v2/json/%s?count=100' % (
            self.service.auth.username,
        )

        user_feed = get_data(
            self.service,
            url,
            disable_oauth=True
        )

        return self._convert_feed(user_feed, since)

    def _convert_feed(self, json, since):
        """Convert the json feed into Service Items limiting on since.
        """

        items = []

        # FIXME add filter on date!
        for entry in json:
            # Check we have a valid feed
            if entry != '404 Not Found':
                item = ServiceItem()
                created = datetime.strptime(entry['dt'], '%Y-%m-%dT%H:%M:%SZ') #'2010-11-23T22:03:29Z'
                if created.date() >= since:
                    try:
                        item.title = entry['d']
                        item.body = entry['n']
                        item.created = created
                        item.link_back = entry['u']
                        item.notes = entry['n']
                        item.tags = entry['t']
                        item.service = self.service

                        if ENABLE_PERSONAL_DATA_STORE:
                            # Generate a unique ID for this item
                            hash.update("%s:%s" % (
                                entry['u'],
                                entry['dt'],
                            ))
                            item.external_service_id = hash.digest()
                        items.append(item)
                    except:
                        pass

        return items
