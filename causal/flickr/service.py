import flickrapi
from datetime import datetime
from django.utils import simplejson
from causal.main.models import ServiceItem, AccessToken
from causal.main.service_utils import get_model_instance

DISPLAY_NAME = 'Flickr'
CUSTOM_FORM = True
OAUTH_FORM = False

def get_items(user, since, model_instance):
    serv = model_instance or get_model_instance(user, __name__)
    items = []

    at = AccessToken.objects.get(service=serv)
    flickr = flickrapi.FlickrAPI(at.api_token)

    photos_json = flickr.photos_search(
        user_id=at.username,
        per_page='10',
        format='json'
    )
    photos_json = photos_json.replace('jsonFlickrApi(', '')
    photos_json = photos_json.rstrip(')')
    photos = simplejson.loads(photos_json)

    for photo in photos['photos']['photo']:
        # flickr.photos.getInfo
        pic = flickr.photos_getInfo(photo_id=photo['id'], format='json')
        pic = pic.replace('jsonFlickrApi(', '')
        pic = pic.rstrip(')')
        p = simplejson.loads(pic)
        epoch = p['photo']['dateuploaded']

        item = ServiceItem()
        item.title = p['photo']['title']['_content']
        item.body = p['photo']['urls']['url'][0]['_content']
        item.created = datetime.fromtimestamp(float(epoch))
        item.service = serv
        items.append(item)
    return items