"""Test suite for delicious services."""

from bunch import Bunch
from causal.main.models import UserService
from causal.facebook.service import ServiceHandler
from datetime import datetime, timedelta, date
from django.utils import simplejson
from django.test import TestCase
import os, time

try:
    import wingdbstub
except ImportError:
    pass

class TestFacebookService(TestCase):
    """Test the module with fixtures."""

    def setUp(self):
        self.path = os.path.dirname(os.path.realpath(__file__))
        self.handler = ServiceHandler(model_instance=UserService())
        self.since =  date.today() - timedelta(days=7)
        
    def tearDown(self):
        pass

    def test_convert_status_feed(self):
        """Test we can convert statuses from facebook."""
         
        test_statuses = []

        item_since = int(time.mktime(datetime.now().timetuple()))
        
        for i in range(0,5):
            b = Bunch(message='Syn %s' %(str(i)), status_id=i, time=item_since, uid=i)
            test_statuses.append(b)
        
        service_items = self.handler._convert_status_feed(test_statuses, 'user', self.since)
        self.assertEqual(len(service_items), 5)

    def test_convert_link_feed(self):
        """Test converting a feed from Facebook into ServiceItems"""
        
        test_links = []
        
        for i in range(0,5):
            entry = Bunch(created_time = int(time.mktime(datetime.now().timetuple())), 
                      owner_comment = 'http://www.bbc.co.uk/news/12318490%s COMMENT' % (str(i)), 
                      summary = 'This is the summary!', 
                      title = 'Title on the page', 
                      url = 'http://www.bbc.co.uk/news/%s/12318490' % (str(i)))

            test_links.append(entry)
            
        service_items = self.handler._convert_link_feed(test_links, self.since)
        self.assertEqual(len(service_items), 5)