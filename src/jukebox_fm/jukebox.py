from os import path, makedirs
from sys import exit
from time import sleep
from argparse import ArgumentParser
from logging import basicConfig, info, error, warning
from toml import load, dump
from mpd import MPDClient
from yt_dlp import YoutubeDL
from requests import get, RequestException

client = MPDClient()

def main():
    args = parse_arguments()
    basicConfig(level=args.l, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config(path.expanduser("~/.config/jukebox-fm/config.toml"))
    music_folder = path.expanduser(config['music']['music_folder'])
    username = args.u or config['lastfm']['username']
    mode = args.m or config['lastfm']['mode']
    endpoint = determine_endpoint(args, username, mode)
    
    try:
        client.connect('localhost', 6600)
        ydl_config = configure_ydl(config, music_folder)
        
        if args.f:
            friends = load_friends(args.f)
            mode = args.m or "library"
            for username in friends:
                fetch_lastfm_data(f"user/{username}/{mode}", music_folder, ydl_config)
        else: 
            fetch_lastfm_data(endpoint, music_folder, ydl_config)

    except KeyboardInterrupt:
        info("Interrupted by user")
    except Exception as e:
        log_error(e)
    finally:
        client.disconnect()

def parse_arguments():
    parser = ArgumentParser(description="Play LastFM music recommendations using: mpd, yt-dlp and python")
    parser.add_argument("-a", help="Play a particular artist")
    parser.add_argument("-g", help="Play a specified genre")
    parser.add_argument("-p", help="Play a specified playlist")
    parser.add_argument("-u", help="Custom LastFM username", default=None)
    parser.add_argument("-m", help="Custom LastFM mode", default=None)
    parser.add_argument("-f", help="Path to LastFM usernames friends.txt", default=None)
    parser.add_argument("-l", help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    return parser.parse_args()

def load_config(config_path):
    if not path.exists(config_path):
        create_default_config(config_path)

    try:
        return load(config_path)
    except Exception as e:
        log_error(f"Could not load configuration file: {e}")

def create_default_config(config_path):
    config_dir = path.dirname(config_path)
    try:
        makedirs(config_dir, exist_ok=True)
    except Exception as e:
        log_error(f"Could not create configuration directory: {e}")

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
        info(f"Created default configuration file at {config_path}")
    except Exception as e:
        log_error(f"Could not create default configuration file: {e}")

def determine_endpoint(args, username, mode):
    if args.a: return f"music/{args.a}"
    elif args.g: return f"tag/{args.g}"
    elif args.p: return f"user/{username}/playlist/{args.p}"
    else: return f"user/{username}/{mode}"
    
def configure_ydl(config, music_folder):
    return {
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

def load_friends(friends_file):
    try:
        with open(friends_file, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        log_error(f"Could not read friends file: {e}")

def fetch_lastfm_data(endpoint, music_folder, ydl_config):
    url = f"https://www.last.fm/player/station/{endpoint}"
    try:
        response = get(url)
        response.raise_for_status()
        playlist = response.json().get("playlist", [])

        if not playlist:
            info("No tracks found in the playlist.")
            return

        parsed_tracks = parse_tracks(playlist)

        info(f"Fetched: {len(parsed_tracks)} tracks")
        for artist, title, playlink_id in parsed_tracks:
            if is_track_in_library(artist, title):
                queue_song(f"{artist} - {title}")
            else:
                download_song(artist, title, playlink_id, music_folder, ydl_config)

    except RequestException as e:
        log_error(f"Can't fetch data from LastFM: {e}")

def parse_tracks(playlist):
    parsed_tracks = []
    for track in playlist:
        try:
            artist = track['artists'][0].get("name")
            title = track.get("name")
            playlink_id = track['_playlinks'][0].get("id")
            if artist and title and playlink_id:
                parsed_tracks.append((artist, title, playlink_id))
            else:
                warning(f"Incomplete track data: {track}")
        except (IndexError, KeyError) as e:
            warning(f"Error parsing track data: {e}")

    return parsed_tracks

def is_track_in_library(artist, title):
    try:
        library = client.listallinfo()
        return any(song['artist'] == artist and song['title'] == title for song in library if 'artist' in song and 'title' in song)
    except Exception as e:
        log_error(f"Could not check library: {e}")
        return False

def queue_song(song):
    try:
        client.update('dl')
        sleep(0.1)
        client.add(f"dl/{song}.opus")
        info(f"Queued: {song}")
    except Exception as e:
        log_error(f"Could not queue song '{song}': {e}")

def download_song(artist, title, playlink_id, music_folder, ydl_config):
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
            queue_song(song)
            info(f"Downloaded and queued: {song}")
        except Exception as e:
            log_error(f"Could not download song '{song}': {e}")

def log_error(message):
    error(message)
    exit(1)

if __name__ == "__main__":
    main()
