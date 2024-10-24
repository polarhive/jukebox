import os
import sys
import requests
from time import sleep
from toml import load
from yt_dlp import YoutubeDL
from mpd import MPDClient

def main():
    client = MPDClient()

    try:
        client.connect('localhost', 6600)
    except Exception as e:
        print(f"ERROR: Can't connect to MPD server: {e}")
        sys.exit(1)

    config_path_user = os.path.expanduser("~/.config/jukebox-fm/config.toml")
    config_path_default = "config.toml"

    try:
        if os.path.exists(config_path_user):
            config = load(config_path_user)
        elif os.path.exists(config_path_default):
            config = load(config_path_default)
        else:
            print("ERROR: No configuration file found.")
            client.disconnect()
            sys.exit(1)

        music_folder = os.path.expanduser(config['music']['music_folder'])
        username = config['lastfm']['username']
        mode = config['lastfm']['mode']
    except KeyError as e:
        print(f"ERROR: Missing configuration key: {e}")
        client.disconnect()
        sys.exit(1)

    ydl_config = {
        'format': config['yt_dlp']['format'],
        'quiet': 'True',
        'noprogress': config['yt_dlp']['quiet'],
        'noplaylist': config['yt_dlp']['noplaylist'],
        'geo_bypass': config['yt_dlp']['geo_bypass'],
        'outtmpl': os.path.join(music_folder, config['yt_dlp']['outtmpl']),
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredquality': config['yt_dlp']['preferred_quality'],
            },
            {'key': 'FFmpegMetadata'}
        ],
    }

    try:
        fetch_lastfm_data(username, mode, client, music_folder, ydl_config)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
    finally:
        client.disconnect()

def fetch_lastfm_data(username, mode, client, music_folder, ydl_config):
    url = f"https://www.last.fm/player/station/user/{username}/{mode}"
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
        sys.exit(1)

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
        client.add(f"dl/{song}.opus")  # Assuming the format is .opus
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
        'outtmpl': os.path.join(music_folder, f'{artist} - {title}'),
    }

    with YoutubeDL(ydl_opts) as ydl:
        song = f"{artist} - {title}"

        try:
            ydl.download([youtube_url])
            client.update('dl')
            sleep(0.1)
            client.add(f"dl/{song}.opus")
            print(f"Downloaded and queued: {song}")

        except Exception as e:
            print(f"ERROR: Could not download or queue song '{song}': {e}")

if __name__ == "__main__":
    main()
