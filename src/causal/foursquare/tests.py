"""Test class for Four Square app.
"""

from causal.foursquare.service import ServiceHandler
from datetime import datetime
from causal.main.models import UserService
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import simplejson
import os

try:
    import wingdbstub
except ImportError:
    pass

class TestFoursquareViews(TestCase):
    """Test the module with fixtures.
    """

    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.handler = ServiceHandler(model_instance=UserService())

    def tearDown(self):
        pass

    def _loadJson(self, name):
        return simplejson.load(file(os.path.join(self.path, 'test_data', name)))

    def test_convert_feed(self):
        """Check we do the right thing for converting
        foursquares feed into ours."""

        json = self._loadJson('user_history.json')

        since = datetime.strptime('Tue, 01 Feb 11 06:40:17 +0000'.replace(' +0000', ''),
                          '%a, %d %b %y %H:%M:%S')

        results = self.handler._convert_feed(json, since.date())

        self.assertEqual(len(results), 3)