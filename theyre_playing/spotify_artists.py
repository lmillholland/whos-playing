"""
Requests and collects all Spotify artists a user listens to. (as defined by one of their tracks being in a playlist)
"""
from django.conf import settings

import os
import requests
import json
import time

class SpotifyArtists:

	def FetchArtists(self, user_id, lineup):
		""" ... """

		self.user_id = user_id
		self.access_token = self.GetAccessToken()

		artist_ids_to_tracks = {
			artist["spotify_id"]: []
			for artist in lineup
		}

		# organize tracks by artist ID
		playlists = self.FetchUserPlaylists()
		for playlist in playlists:
			for track in playlist.FetchTracks(self.access_token):
				for artist_id in track.artist_ids:
					if artist_id in artist_ids_to_tracks:
						if track not in artist_ids_to_tracks[artist_id]:
							artist_ids_to_tracks[artist_id].append(track)

		# prune empty artists
		artist_ids_to_tracks = {
			k: v for k,v in artist_ids_to_tracks.items()
			if len(v) > 0
		}

		# retrieve artist data
		artists = self.FetchAllArtistData(list(artist_ids_to_tracks.keys()))
		for artist in artists:
			artist.tracks = artist_ids_to_tracks[artist.id]

		# clean data
		artists_json = {
			"artists": [
				artist.GetDataAsDict() for artist in artists
				if len(artist.tracks) > 0
			],
			"playlists": [p.name for p in playlists]
		}

		return artists_json


	def FetchAllArtistData(self, artist_ids, artists_data=[]):
		# make request
		id_args = ",".join(artist_ids[:50])
		request_url = "https://api.spotify.com/v1/artists?ids=" + id_args
		headers = {
			'content-type': 'application/json',
			'Authorization': f"Bearer {self.access_token}",
			'Accept-Charset': 'UTF-8'
		}
		response = requests.get(request_url, headers=headers).json()

		# batch response
		artists_data.extend(response.get("artists", []))
		if len(artist_ids) > 50:
			return self.FetchAllArtistData(artist_ids[50:], artists_data)

		return [SpotifyArtist(a) for a in artists_data]


	def FetchUserPlaylists(self, request_url=None, playlists=[]):
		""" Get all user playlists. """
		if request_url == None:
			request_url = f"https://api.spotify.com/v1/users/{self.user_id}/playlists"

		headers = {
			'content-type': 'application/json',
			'Authorization': f"Bearer {self.access_token}",
			'Accept-Charset': 'UTF-8'
		}
		response = requests.get(request_url, headers=headers).json()

		# parse playlists
		for playlist_data in response.get('items', []):
			playlist = SpotifyPlaylist(playlist_data)
			playlists.append(playlist)

		# proceed to next batch, or exit
		if response.get('next') != None:
			return self.GetUserPlaylists(response['next'], playlists)

		return playlists


	@staticmethod
	def GetAccessToken():
		""" The access token is a string which contains the credentials and permissions that can be 
		used to access a given resource (e.g artists, albums or tracks) or user's data (e.g your profile 
		or your playlists). """
		client_id = 'f54d6dccf417422aa80723f0d1bdf4ee'

		credentials_filepath = os.path.join(settings.BASE_DIR, 'theyre_playing/static/credentials.json')
		if os.path.isfile(credentials_filepath):
			with open(credentials_filepath, "r") as file:
				client_secret = json.load(file)["spotify_secret"]
		else:
			client_secret = os.environ.get("SPOTIFY_SECRET")

		url = 'https://accounts.spotify.com/api/token'
		payload = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
		headers = {'content-type': 'application/x-www-form-urlencoded', 'Accept-Charset': 'UTF-8'}
		response = requests.post(url, data=payload, headers=headers)

		return response.json()['access_token']



class SpotifyPlaylist:

	def __init__(self, json_data):
		self.id = json_data['id']
		self.name = json_data['name']
		self.owner = json_data['owner']


	def FetchTracks(self, access_token, request_url=None, tracks=[]):
		""" Load tracks from this playlist, along with the artist. """
		if request_url is None:
			request_url = f"https://api.spotify.com/v1/playlists/{self.id}/tracks"

		headers = {
			'content-type': 'application/json',
			'Authorization': f"Bearer {access_token}",
			'Accept-Charset': 'UTF-8'
		}
		response = requests.get(request_url, headers=headers).json()

		for item in response['items']:
			track = SpotifyTrack(item['track'])
			tracks.append(track)

		if response["next"] != None:
			return self.FetchTracks(access_token, response["next"], tracks)

		return tracks



class SpotifyTrack:

	def __init__(self, track_data):
		self.id = track_data['id']
		self.name = track_data['name']
		self.popularity = track_data.get('popularity', 0)
		self.href = track_data.get('external_urls', {}).get('spotify', None)
		try:
			self.image_url = track_data.get('album', {}).get('images', [{}])[0].get('url')
		except:
			self.image_url = None
		self.artist_ids = [artist["id"] for artist in track_data['artists']]

	def __eq__(self, other):
		return self.id == other.id

	def GetDataAsDict(self):
		data = {
			"name": self.name,
			"popularity": self.popularity,
			"href": self.href,
			"image_url": self.image_url
		}
		return data



class SpotifyArtist:

	def __init__(self, artist_json):
		self.id = artist_json['id']
		self.name = artist_json['name']
		self.popularity = artist_json["popularity"]
		self.href = artist_json.get("external_urls", {}).get("spotify")
		try:
			self.image_url = artist_json.get("images", [{}])[0].get("url", None)
		except:
			self.image_url = None
		self.genres = artist_json["genres"]
		self.tracks = []

	def __eq__(self, other):
		return self.id == other.id

	def GetDataAsDict(self):
		data = {
			"name": self.name,
			"popularity": self.popularity,
			"href": self.href,
			"image_url": self.image_url,
			"genres": self.genres,
			"tracks": [track.GetDataAsDict() for track in self.tracks]
		}
		return data



def get_venue_lineup():
	filepath = "static/data/lineup.json"
	with open(filepath, 'r') as file:
		return json.load(file)["lineup"]


if __name__ == "__main__":
	spotify_artists = SpotifyArtists().FetchArtists("630washington", get_venue_lineup())
	print(json.dumps(spotify_artists, indent=2))

	'''
	with open("cached_artists_TIAN.json", "w+", encoding='utf-8') as f:
		json.dump(spotify_artists, f, ensure_ascii=False, indent=4)
	'''
