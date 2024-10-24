import os
import sys
import requests
import toml
import time
from yt_dlp import YoutubeDL
from mpd import MPDClient

client = MPDClient()
client.connect('localhost', 6600)

# config
config = toml.load("config.toml")
music_folder = os.path.expanduser(config['music']['music_folder'])
username = config['lastfm']['username']
mode = config['lastfm']['mode']

def fetch_lastfm_data(username, mode):
    url = f"https://www.last.fm/player/station/user/{username}/{mode}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        playlist = response.json().get("playlist", [])
        parsed_tracks = [
            (track['artists'][0].get("name"), track.get("name"), track['_playlinks'][0].get("id"))
            for track in playlist if track.get("artists") and track.get("_playlinks")
        ]

        for artist, title, playlink_id in parsed_tracks:
            download_and_queue_song(artist, title, playlink_id)

    except requests.RequestException as e:
        print(f"ERROR: Can't fetch data from LastFM: {e}")
        sys.exit(1)

def download_and_queue_song(artist, title, playlink_id):

    youtube_url = f"https://www.youtube.com/watch?v={playlink_id}"
    ydl_opts = {
        'format': 'opus/bestaudio',
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'opus', 'preferredquality': '192'},
            {'key': 'FFmpegMetadata'}
        ],
        'outtmpl': os.path.join(music_folder, f'{artist} - {title}'),
        'postprocessor_args': [
            '-metadata', f'title={title}',
            '-metadata', f'artist={artist}',
        ],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
        client.update('dl')
        time.sleep(0.1)
        song=f"{artist} - {title}"
        print(f"queueing: {song}")
        client.add(f"dl/{song}.opus")


def main():
    fetch_lastfm_data(username, mode)
    client.disconnect()

if __name__ == "__main__":
    main()
