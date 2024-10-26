import requests
from os import path, makedirs
from sys import exit
from time import sleep
from toml import load, dump
from yt_dlp import YoutubeDL
from mpd import MPDClient
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description="Welcome to jukebox")
    parser.add_argument("-a", "--artist", help="Play a particular artist")
    parser.add_argument("-g", "--genre", help="Play a specified genre")
    parser.add_argument("-p", "--playlist", help="Play a specified playlist")
    parser.add_argument("-u", "--username", help="Custom LastFM username", default=None)
    parser.add_argument("-m", "--mode", help="Custom LastFM mode", default=None)
    args = parser.parse_args()

    # load toml config
    config_path_user = path.expanduser("~/.config/jukebox-fm/config.toml")
    client = MPDClient()

    # ifnot? create a default one
    if not path.exists(config_path_user):
        create_default_config(config_path_user)

    try:
        if path.exists(config_path_user): config = load(config_path_user)
        else: print("ERROR: No configuration file found."); exit(1)

        # mapping
        music_folder = path.expanduser(config['music']['music_folder'])
        username = args.username if args.username else config['lastfm']['username']
        mode = args.mode if args.mode else config['lastfm']['mode']

    except KeyError as e: print(f"ERROR: Missing configuration key: {e}"); exit(1)

    # set endpoints
    if args.artist: endpoint = f"music/{args.artist}"
    elif args.genre: endpoint = f"tag/{args.genre}"
    elif args.playlist: endpoint = f"user/{username}/playlist/{args.playlist}"
    else: endpoint = f"user/{username}/{mode}"

    try:
        client.connect('localhost', 6600)
        ydl_config = {
            'format': config['yt_dlp']['format'],
            'quiet': True,
            'noprogress': config['yt_dlp']['quiet'],
            'noplaylist': config['yt_dlp']['noplaylist'],
            'geo_bypass': config['yt_dlp']['geo_bypass'],
            'outtmpl': path.join(music_folder, config['yt_dlp']['outtmpl']),
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredquality': config['yt_dlp']['preferred_quality']},
                {'key': 'FFmpegMetadata'}
            ],
        }
        fetch_lastfm_data(endpoint, client, music_folder, ydl_config)

    except KeyboardInterrupt: print("\n[QUIT] Interrupted by user")
    except Exception as e: print(f"ERROR: {e}")
    finally: client.disconnect()

def create_default_config(config_path):
    config_dir = path.dirname(config_path)
    try: makedirs(config_dir, exist_ok=True)
    except Exception as e: print(f"ERROR: Could not create configuration directory: {e}"); exit(1)

    default_config = {
        'music': {'music_folder': '~/Music/dl'},
        'lastfm': {'username': 'lastfm', 'mode': 'mix'},
        'yt_dlp': {
            'format': 'opus/bestaudio',
            'quiet': True,
            'noplaylist': True,
            'geo_bypass': True,
            'outtmpl': '%(artist)s - %(title)s',
            'preferred_quality': '192'
        }
    }
    try:
        with open(config_path, 'w') as config_file:
            dump(default_config, config_file)
        print(f"Created default configuration file at {config_path}")
    except Exception as e:
        print(f"ERROR: Could not create default configuration file: {e}")
        exit(1)

def fetch_lastfm_data(endpoint, client, music_folder, ydl_config):
    url = f"https://www.last.fm/player/station/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        playlist = response.json().get("playlist", [])

        if not playlist:
            print("No tracks found in the playlist.")
            return

        parsed_tracks = []
        for track in playlist:
            try:
                artist = track['artists'][0].get("name")
                title = track.get("name")
                playlink_id = track['_playlinks'][0].get("id")
                if artist and title and playlink_id:
                    parsed_tracks.append((artist, title, playlink_id))
                else:
                    print(f"WARNING: Incomplete track data: {track}")
            except (IndexError, KeyError) as e:
                print(f"WARNING: Error parsing track data: {e}")

        print(f"Fetched: {len(parsed_tracks)} tracks")
        for artist, title, playlink_id in parsed_tracks:
            if is_track_in_library(artist, title, client):
                queue_song(artist, title, client)
            else:
                download_and_queue_song(artist, title, playlink_id, client, music_folder, ydl_config)

    except requests.RequestException as e:
        print(f"ERROR: Can't fetch data from LastFM: {e}")
        exit(1)

def is_track_in_library(artist, title, client):
    try:
        library = client.listallinfo()
        for song in library:
            if 'artist' in song and 'title' in song:
                if song['artist'] == artist and song['title'] == title:
                    return True
    except Exception as e:
        print(f"ERROR: Could not check library: {e}")
    return False

def queue_song(artist, title, client):
    song = f"{artist} - {title}"
    try:
        client.update('dl')
        sleep(0.1)
        client.add(f"dl/{song}.opus")
        print(f"Queued: {song}")
    except Exception as e:
        print(f"ERROR: Could not queue song '{song}': {e}")

def download_and_queue_song(artist, title, playlink_id, client, music_folder, ydl_config):
    youtube_url = f"https://www.youtube.com/watch?v={playlink_id}"
    ydl_opts = {
        **ydl_config,
        'postprocessor_args': [
            '-metadata', f'title={title}',
            '-metadata', f'artist={artist}',
        ],
        'outtmpl': path.join(music_folder, f'{artist} - {title}'),
    }

    with YoutubeDL(ydl_opts) as ydl:
        song = f"{artist} - {title}"

        try:
            ydl.download([youtube_url])
            try:
                client.update('dl')
                sleep(0.1)
                client.add(f"dl/{song}.opus")
                print(f"Downloaded and queued: {song}")
            except Exception as e:
                print(f"ERROR: Could not queue song '{song}': {e}")
        except Exception as e:
            print(f"ERROR: Could not download song '{song}': {e}")

if __name__ == "__main__":
    main()
