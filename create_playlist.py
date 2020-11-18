import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl

from exceptions import ResponseException
from secrets import spotify_token, spotify_user_id


class CreatePlaylist:
    def __init__(self):
        self.youtube_client = self.get_youtube_client()
        self.musicas_info = {}

    def get_youtube_client(self):
        # obs: copiado da documentação do Youtube Data API
        
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def get_liked_videos(self):

        request = self.youtube_client.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        resposta = request.execute()


        for item in resposta["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(
                item["id"])

            video = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            if song_name is not None and artist is not None:

                self.musicas_info[video_title] = {
                    "youtube_url": youtube_url,
                    "song_name": song_name,
                    "artist": artist,
                    "spotify_uri": self.get_spotify_uri(song_name, artist)
                }

    def criar_playlist(self):
        request_body = json.dumps({
            "name": "Playlist do Youtube",
            "description": "Todos os vídeos da playlist",
            "public": True })

        query = "https://api.spotify.com/v1/users/{}/playlists".
            format(spotify_user_id)
        resposta = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            })
        
        resposta_json = resposta.json()

        # id da playlist
        return resposta_json["id"]

    def get_spotify_uri(self, song_name, artist):
        # buscar musica
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".
            format(
                song_name,
                artist
            )
        resposta = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        resposta_json = resposta.json()
        musicas = resposta_json["tracks"]["items"]

        #link para a primeira musica da playlist
        return musicas[0]["uri"]

    def adicionar_musicas(self):
        #Adiciona as musicas a uma nova playlist
        
        self.get_liked_videos()

        playlist_id = self.criar_playlist()
        
        uris = [info["spotify_uri"]
                for song, info in self.musicas_info.items()]



        #adiciona musicas na playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(
            playlist_id)

        resposta = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        if resposta.status_code != 200:
            raise ResponseException(resposta.status_code)

        resposta_json = resposta.json()
        return resposta_json


if __name__ == '__main__':
    teste = CreatePlaylist()
    teste.adicionar_musicas()
