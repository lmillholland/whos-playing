"""
Requests and collects all Spotify artists a user listens to. (as defined by one of their tracks being in a playlist)
"""
import os
import requests
import json
import time

CLIENT_ID = 'f54d6dccf417422aa80723f0d1bdf4ee'
CLIENT_SECRET = '2586b8f249294201ad4902f5a8ab02e8'
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET", "localhost,127.0.0.1,[::1]").split(",")

CACHE_FILE_NAME = "artists.txt"

class SpotifyArtists:

	def FetchArtists(self, user_id):
		access_token = self.GetAccessToken(CLIENT_ID, CLIENT_SECRET)
		playlists = self.FetchUserPlaylists(access_token, f"https://api.spotify.com/v1/users/{user_id}/playlists")
		access_token = self.GetAccessToken(CLIENT_ID, CLIENT_SECRET)
		artists = self.OrganizeTracksByArtist(playlists, access_token)
		artists_json = {
			"artists": [artist.GetDataAsDict() for artist in artists],
			"playlists": [p.name for p in playlists]
		}

		return artists_json
	

	def OrganizeTracksByArtist(self, playlists, access_token):
		# get all unique tracks
		tracks = list()
		for playlist in playlists:
			playlist_tracks = playlist.FetchTracks(access_token)
			for track in playlist_tracks:
				if track not in tracks:
					tracks.append(track)

		# get all artist ids (unique)
		artist_ids = list()
		for track in tracks:
			for artist_id in track.artist_ids:
				if artist_id != None:
					if artist_id not in artist_ids:
						artist_ids.append(artist_id)

		# get all artist data
		all_artist_data = self.FetchAllArtistsData(access_token, artist_ids)
		artists = [SpotifyArtist(a) for a in all_artist_data]

		# add tracks to artists
		for artist in artists:
			for track in tracks:
				if artist.id in track.artist_ids:
					if track not in artist.tracks:
						artist.tracks.append(track)

		return artists


	def FetchAllArtistsData(self, access_token, artist_ids, artists_data=[]):
		# make request
		id_args = ",".join(artist_ids[:50])
		request_url = "https://api.spotify.com/v1/artists?ids=" + id_args
		headers = {
			'content-type': 'application/json',
			'Authorization': f"Bearer {access_token}",
			'Accept-Charset': 'UTF-8'
		}
		response = requests.get(request_url, headers=headers).json()

		# batch response
		artists_data.extend(response.get("artists", []))
		if len(artist_ids) > 50:
			return self.FetchAllArtistsData(access_token, artist_ids[50:], artists_data)

		return artists_data

	def FetchArtist(self, access_token, artist_id):
		# obsolete: please use FetchAllArtistsData instead, for batching purposes
		request_url = "https://api.spotify.com/v1/artists/" + artist_id
		headers = {
			'content-type': 'application/json',
			'Authorization': f"Bearer {access_token}",
			'Accept-Charset': 'UTF-8'
		}
		response = requests.get(request_url, headers=headers).json()

		return SpotifyArtist(response)


	def FetchUserPlaylists(self, access_token, request_url, playlists=[]):
		""" Get all user playlists. """
		headers = {
			'content-type': 'application/json',
			'Authorization': f"Bearer {access_token}",
			'Accept-Charset': 'UTF-8'
		}
		response = requests.get(request_url, headers=headers).json()

		# parse playlists
		for playlist_data in response['items']:
			playlist = SpotifyPlaylist(playlist_data)
			playlists.append(playlist)

		# proceed to next batch, or exit
		if response['next'] != None:
			return self.GetUserPlaylists(access_token, response['next'], playlists)

		return playlists


	def GetAccessToken(self, client_id, client_secret):
		""" The access token is a string which contains the credentials and permissions that can be 
		used to access a given resource (e.g artists, albums or tracks) or user's data (e.g your profile 
		or your playlists). """
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



if __name__ == "__main__":
	spotify_artists = SpotifyArtists().FetchArtists("tscwnvw")
	with open("cached_artists_TIAN.json", "w+", encoding='utf-8') as f:
		json.dump(spotify_artists, f, ensure_ascii=False, indent=4)
