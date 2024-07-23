import requests
import json
import os

from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .spotify_artists import SpotifyArtists


def index(request):


	return HttpResponse(os.environ.get("SPOTIFY_SECRET"))

	template = loader.get_template('index.html')

	context = {
        'num_spotify_artists': 3
    }

	return HttpResponse(template.render(context))


def get_cached_spotify_artists(filename):
	filepath = os.path.join(settings.BASE_DIR, 'theyre_playing/static/data/' + filename + '.json')
	with open(filepath, 'r') as file:
		return json.load(file)


def get_venue_lineup():
	filepath = os.path.join(settings.BASE_DIR, 'theyre_playing/static/data/lineup.json')
	with open(filepath, 'r') as file:
		return json.load(file)["lineup"]


@csrf_exempt
def find_artists(request):
	if request.method == 'POST':
		# fetch spotify data
		spotify_username = request.POST.get('textfield', None)
		spotify_data = SpotifyArtists().FetchArtists(spotify_username)

		'''
		if spotify_username == "630washington":
			spotify_data = get_cached_spotify_artists("cached_artists")
		if spotify_username == "tscwnvw":
			spotify_data = get_cached_spotify_artists("cached_artists_TIAN")
		else:
			spotify_data = SpotifyArtists().FetchArtists(spotify_username)
		'''

		# compare to venue
		venue_artists = [x.lower() for x in get_venue_lineup()]
		data = {
			"artists": [a for a in spotify_data["artists"] if a["name"].lower() in venue_artists],
			"playlists": spotify_data["playlists"],
			"username": spotify_username
		}

		template = loader.get_template('overlapping_artists.html')
		return HttpResponse(template.render(data))

	return render(request, 'template.html', locals())
