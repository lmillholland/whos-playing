"""
Get Spotify artist IDs for festival lineup.
"""
import requests
import json

from spotify_artists import SpotifyArtists

class Lineup:

	def __init__(self, artist_names):
		access_token = SpotifyArtists.GetAccessToken()

		self.artists = []
		for artist_name in artist_names:
			# get data
			request_url = f"https://api.spotify.com/v1/search?query={artist_name}&type=artist&locale=en-US"
			headers = {
				'content-type': 'application/json',
				'Authorization': f"Bearer {access_token}",
				'Accept-Charset': 'UTF-8'
			}
			response = requests.get(request_url, headers=headers).json()

			# find id
			artist_id = None
			for result in response["artists"]["items"]:
				if result["name"].casefold() == artist_name.casefold():
					artist_id = result["id"]
					break

			# record
			artist = LineupArtist(artist_name, artist_id)
			if artist_id is not None:
				self.artists.append(artist)


class LineupArtist:

	def __init__(self, artist_name, artist_spotify_id):
		self.name = artist_name
		self.spotify_id = artist_spotify_id

	def __str__(self):
		return f"{self.name} ({self.spotify_id})"


if __name__ == "__main__":
	with open("static/data/lineup.json", "r") as file:
		artist_names = json.load(file)["lineup"]
	lineup = Lineup(artist_names)
	with open("static/data/lineup_NEW", "w+") as file:
		data = {
			"lineup": [
				{
					"name": artist.name,
					"spotify_id": artist.spotify_id
				}
				for artist in lineup.artists
			]
		}
		json.dump(data, file)

