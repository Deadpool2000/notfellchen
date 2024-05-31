import requests
import json
from notfellchen import __version__ as nf_version
from fellchensammlung.models import Location

from math import radians, sqrt, sin, cos, atan2


def calculate_distance_between_coordinates(position1, position2):
    """
    Calculate the distance between two points identified by coordinates
    It expects the coordinates to be a tuple (lat, lon)

    Based on https://en.wikipedia.org/wiki/Haversine_formula
    """
    earth_radius_km = 6371
    latitude1 = float(position1[0])
    longitude1 = float(position1[1])
    latitude2 = float(position2[0])
    longitude2 = float(position2[1])

    distance_lat = radians(latitude2 - latitude1)
    distance_long = radians(longitude2 - longitude1)

    a = pow(sin(distance_lat / 2), 2) + cos(radians(latitude1)) * cos(radians(latitude2)) * pow(sin(distance_long / 2),
                                                                                                2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance_in_km = earth_radius_km * c

    return distance_in_km


class ResponseMock:
    content = b'[{"place_id":138181499,"licence":"Data \xc2\xa9 OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright","osm_type":"relation","osm_id":1247237,"lat":"48.4949904","lon":"9.040330235970146","category":"boundary","type":"postal_code","place_rank":21, "importance":0.12006895017929346,"addresstype":"postcode","name":"72072","display_name":"72072, Derendingen, T\xc3\xbcbingen, Landkreis T\xc3\xbcbingen, Baden-W\xc3\xbcrttemberg, Deutschland", "boundingbox":["48.4949404","48.4950404","9.0402802","9.0403802"]}]'
    status_code = 200

    def json(self):
        return json.loads(self.content.decode())


class RequestMock:
    @staticmethod
    def get(url, params=None, data=None, headers=None):
        return ResponseMock()


class GeoAPI:
    api_url = "https://nominatim.openstreetmap.org/search"
    headers = {
        'User-Agent': f"Notfellchen {nf_version}",
        'From': 'info@notfellchen.org'  # This is another valid field
    }

    def __init__(self, debug=True):
        if debug:
            self.requests = RequestMock
        else:
            self.requests = requests

    def get_coordinates_from_postcode(self, postcode):
        result = self.requests.get(self.api_url, {"q": postcode, "format": "jsonv2"}, headers=self.headers).json()[0]
        return result["lat"], result["lon"]

    def get_location_from_string(self, location_string):
        result = self.requests.get(self.api_url, {"q": location_string, "format": "jsonv2"}, headers=self.headers).json()[0]
        location = Location.objects.create(
            place_id=result["place_id"],
            osm_id=result["osm_id"],
            latitude=result["lat"],
            longitude=result["lon"],
            name=result["name"],
        )
        return location


if __name__ == "__main__":
    geo = GeoAPI(debug=True)
    print(geo.get_coordinates_from_postcode("72072"))
    print(calculate_distance_between_coordinates(('48.4949904', '9.040330235970146'), ("48.648333", "9.451111")))
