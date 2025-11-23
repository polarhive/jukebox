from os import path, makedirs, devnull, open as os_open, O_WRONLY, dup, dup2
from sys import exit, stderr
from time import sleep
from argparse import ArgumentParser
from logging import (
    basicConfig,
    info,
    error,
    warning,
    StreamHandler,
    Formatter,
    getLogger,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
)
from toml import load, dump
from mpd import MPDClient
from yt_dlp import YoutubeDL
from subprocess import run
from shutil import which
from requests import get, RequestException
from importlib import metadata
from tqdm import tqdm

client = MPDClient()


def main():
    args = parse_arguments()
    if getattr(args, "version", False) or getattr(args, "v", False):
        print_version_and_exit()
    config_dir = init()

    # toml
    config = load_config(path.join(config_dir, "config.toml"))
    logger(config, args)
    music_folder = path.expanduser(config["music"]["music_folder"])
    username = args.u if args.u else config["lastfm"]["username"]
    mode = args.m if args.m else config["lastfm"]["mode"]
    global download_mode
    if not args.d:
        download_mode = False

    if args.b or args.o:
        global api_key
        api_key = config["lastfm"]["API_KEY"]
        if not api_key:
            error("empty API_KEY")
            exit(1)

    if args.o:
        download_mode = True
        info("Loved tracks mode is on")

    if args.d:
        if not args.b:
            error("Download mode cannot be used without -b.")
            exit(1)
        else:
            download_mode = True
            info("Download mode is on")

    friends = args.f  # friend mode enabled
    endpoint = determine_endpoint(args, username, mode)

    # check if we can connect to the local MPD server
    try:
        client.connect("localhost", 6600)
        ydl_config = configure_ydl(config, music_folder)

        if args.f:
            if friends == True:  # -f but no path override
                friends = path.expanduser(config["friends"]["friends_file"])
            friends = load_friends(friends)
            mode = args.m or "library"
            for username in friends:
                info(f"fetching: {username}")
                fetch_lastfm_data(f"user/{username}/{mode}", music_folder, ydl_config, config)

        elif args.o:
            download_loved_tracks(username, music_folder, ydl_config, config)

        elif download_mode:
            max_albums = None
            if config and "lastfm" in config:
                max_albums = config["lastfm"].get("max_albums")
            
            albums_to_process = albums
            if max_albums and len(albums) > max_albums:
                info(f"Limiting to {max_albums} albums (found {len(albums)})")
                albums_to_process = albums[:max_albums]
            
            for i, (name, _) in enumerate(albums_to_process):
                info(f"{i+1}/{len(albums_to_process)}: {name}")
                selected_name, _ = albums_to_process[i]
                selected_url = next(
                    url for name, url in albums if name == selected_name
                )
                endpoint = selected_url.replace("https://www.last.fm/", "")
                fetch_lastfm_data(endpoint, music_folder, ydl_config, config)

        else:
            fetch_lastfm_data(endpoint, music_folder, ydl_config, config)

    except KeyboardInterrupt:
        info("Interrupted by user")
    except Exception as e:
        log_error(e)
    finally:
        client.disconnect()


class ColoredFormatter(Formatter):
    COLORS = {
        DEBUG: '\033[36m',      # Cyan
        INFO: '\033[32m',       # Green
        WARNING: '\033[33m',    # Yellow
        ERROR: '\033[31m',      # Red
        CRITICAL: '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        levelname = record.levelname
        if record.levelno in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelno]}{self.BOLD}{levelname}{self.RESET}"

        result = super().format(record)
        record.levelname = levelname
        return result


def logger(config, args):
    log_file = "/tmp/jukebox-fm.log"
    try:
        cfg_log = config.get("logging", {}).get("log_file")
        if cfg_log:
            log_file = path.expanduser(cfg_log)
    except Exception:
        pass
    basicConfig(
        level=args.l,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename=log_file,
        filemode="a",
    )
    console_handler = StreamHandler()
    console_handler.setLevel(args.l)
    console_handler.setFormatter(ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s"))
    getLogger().addHandler(console_handler)
    info(f"Log file: {log_file}")


def parse_arguments():
    parser = ArgumentParser(
        description="Play LastFM music recommendations using: mpd, yt-dlp and python"
    )
    parser.add_argument(
        "-b", metavar="VALUES", type=str, help="Search albums by artist"
    )
    parser.add_argument("-d", action="store_true", help="Enable download mode.")
    parser.add_argument("-a", help="Play a particular artist")
    parser.add_argument("-g", help="Play a specified genre")
    parser.add_argument("-p", help="Play a specified playlist")
    parser.add_argument("-u", help="Custom LastFM username", default=None)
    parser.add_argument("-m", help="Custom LastFM mode", default=None)
    parser.add_argument(
        "-o", action="store_true", help="Download user's loved tracks from LastFM"
    )
    parser.add_argument(
        "-f",
        help="Path to LastFM usernames friends.txt",
        nargs="?",
        const=True,
        default=None,
    )
    parser.add_argument(
        "-l",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show program version and exit",
    )
    return parser.parse_args()


def init():
    config_dir = path.expanduser("~/.config/jukebox-fm")
    if not path.exists(config_dir):
        warning("It looks like this is your first time running jukebox!")
        warning("Please run the setup script:")
        warning(
            "curl -fsSL https://raw.githubusercontent.com/polarhive/jukebox/refs/heads/main/setup.sh | bash"
        )
        exit(1)
    return config_dir


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
        "music": {"music_folder": "~/Music/dl"},
        "lastfm": {
            "username": "lastfm",
            "mode": "mix",
            "API_KEY": "",  # Get your API key from https://www.last.fm/api/accounts
            # Limits (only used when API_KEY is set)
            "loved_tracks_limit": 50,  # Max loved tracks to fetch with -o flag
            "max_tracks": 50,  # Max tracks to download from playlists/stations
            "max_albums": 10,  # Max albums to download when using -b with -d
        },
        "yt_dlp": {
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "preferred_quality": "192",
            "format": "opus/bestaudio",
            "outtmpl": "%(artist)s - %(title)s",
            # Optional path to a cookies.txt (Netscape) file to pass to yt-dlp
            # Example: "~/.config/jukebox-fm/cookies.txt"
            "cookies": "",
        },
        "friends": {"friends_file": "~/.config/jukebox-fm/friends.txt"},
        "logging": {"log_file": "/tmp/jukebox-fm.log"},
    }

    try:
        with open(config_path, "w") as config_file:
            dump(default_config, config_file)
        info(f"Created default configuration file at {config_path}")
    except Exception as e:
        log_error(f"Could not create default configuration file: {e}")


def album(artist_name):
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "artist.gettopalbums",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json",
    }

    response = get(url, params=params)
    if response.status_code != 200:
        log_error("Failed to fetch albums from Last.fm")
        return None

    albums = []
    for album in response.json().get("topalbums", {}).get("album", []):
        album_name = album.get("name", "").strip()
        if album_name and album_name.lower() != "(null)":
            album_url = f"https://www.last.fm/music/{artist_name.replace(' ', '+')}/{album_name.replace(' ', '+')}"
            albums.append((album_name, album_url))

    if not albums:
        log_error("No valid albums found for this artist.")
        return None
    elif not download_mode:
        fzf_exists = which("fzf") is not None
        if fzf_exists:
            album_names = [name for name, _ in albums]
            try:
                info("Launching fzf for album selection...")
                result = run(
                    ["fzf"],
                    input="\n".join(album_names),
                    text=True,
                    capture_output=True,
                )
                selected_name = result.stdout.strip()
                if not selected_name:
                    warning("No album selected.")
                    return None
                selected_url = next(
                    url for name, url in albums if name == selected_name
                )
                return selected_url
            except Exception as e:
                error(f"Error running fzf: {e}")
                return None
        else:
            print("Available Albums:")
            for i, (name, _) in enumerate(albums):
                print(f"{i}. {name}")
            while True:
                try:
                    choice = int(input("\nSelect an album (by number): "))
                    selected_name, _ = albums[choice]
                    selected_url = next(
                        url for name, url in albums if name == selected_name
                    )
                    return selected_url
                except (ValueError, IndexError):
                    print("Invalid selection. Please choose a valid album number.")
    else:
        return albums


def fetch_loved_tracks(username, config=None):
    limit = 50
    if config and "lastfm" in config:
        limit = config["lastfm"].get("loved_tracks_limit", config["lastfm"].get("limit", 50))

    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.getlovedtracks",
        "user": username,
        "api_key": api_key,
        "format": "json",
        "limit": limit,
    }

    try:
        response = get(url, params=params)
        response.raise_for_status()

        data = response.json()
        loved_tracks = data.get("lovedtracks", {}).get("track", [])

        if not loved_tracks:
            info("No loved tracks found.")
            return []

        tracks = []
        for track in loved_tracks:
            try:
                artist_name = track.get("artist", {}).get("name", "")
                track_name = track.get("name", "")
                if artist_name and track_name:
                    tracks.append((artist_name, track_name))
                    info(f"Found loved track: {artist_name} - {track_name}")
            except (TypeError, KeyError) as e:
                warning(f"Error parsing loved track data: {e}")

        info(f"Total loved tracks found: {len(tracks)}")
        return tracks

    except RequestException as e:
        log_error(f"Failed to fetch loved tracks from Last.fm: {e}")
        return []


def determine_endpoint(args, username, mode):
    if args.a:
        return f"music/{args.a}"
    elif args.b:
        if args.d:
            global albums
            albums = album(args.b)
        else:
            args.p = album(args.b)
    elif args.g:
        return f"tag/{args.g}"
    if args.p:
        return args.p.replace("https://www.last.fm/", "")
    else:
        return f"user/{username}/{mode}"


def configure_ydl(config, music_folder):
    ydl_opts = {
        "format": config["yt_dlp"]["format"],
        "quiet": True,
        "noprogress": config["yt_dlp"]["quiet"],
        "noplaylist": config["yt_dlp"]["noplaylist"],
        "geo_bypass": config["yt_dlp"]["geo_bypass"],
        "outtmpl": path.join(music_folder, config["yt_dlp"]["outtmpl"]),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredquality": config["yt_dlp"]["preferred_quality"],
            },
            {"key": "FFmpegMetadata"},
        ],
    }

    # If a cookies file is provided in the config, pass it to yt-dlp
    try:
        cookies_path = config.get("yt_dlp", {}).get("cookies", "")
        if cookies_path:
            cookies_path = path.expanduser(cookies_path)
            if path.exists(cookies_path):
                ydl_opts["cookiefile"] = cookies_path
                info(f"Using cookies file for yt-dlp: {cookies_path}")
            else:
                warning(f"Configured cookies file not found: {cookies_path}")
    except Exception as e:
        warning(f"Error while processing cookies config: {e}")

    try:
        remote_components = config.get("yt_dlp", {}).get("remote_components", "")
        if remote_components:
            if isinstance(remote_components, str):
                remote_components = [remote_components]
            ydl_opts["remote_components"] = remote_components
            info(f"Using remote components for yt-dlp: {remote_components}")
    except Exception as e:
        warning(f"Error while processing remote_components config: {e}")

    return ydl_opts


def download_loved_tracks(username, music_folder, ydl_config, config=None):
    """Download all loved tracks for a user"""
    info(f"Fetching loved tracks for user: {username}")
    loved_tracks = fetch_loved_tracks(username, config)

    if not loved_tracks:
        info("No loved tracks to download.")
        return

    info(f"Starting download of {len(loved_tracks)} loved tracks...")
    
    try:
        library_cache = client.listallinfo()
        info(f"Library cached: {len(library_cache)} items")
    except Exception as e:
        warning(f"Could not cache library: {e}")
        library_cache = []

    for i, (artist, title) in enumerate(loved_tracks, 1):
        info(f"Processing {i}/{len(loved_tracks)}: {artist} - {title}")
        song_name = f"{artist} - {title}"

        # Check if track exists in library and get its file path
        file_path = is_track_in_library(artist, title, library_cache)
        if file_path:
            try:
                client.add(file_path)
                info(f"Queued: {song_name}")
                continue
            except Exception as e:
                warning(f"Found in library but couldn't queue '{song_name}': {e}")

        # Search for the track on YouTube and download
        download_song(artist, title, music_folder, ydl_config, return_success=True)

    info("Finished processing loved tracks.")


def load_friends(friends_file):
    try:
        with open(friends_file, "r") as file:
            lines = [line.strip() for line in file if line.strip()]
            if not lines:
                log_error("friends.txt empty.")
            else:
                return lines
    except Exception as e:
        log_error(f"Could not read friends.txt: {e}")


def fetch_lastfm_data(endpoint, music_folder, ydl_config, config=None):
    url = f"https://www.last.fm/player/station/{endpoint}"
    try:
        response = get(url)
        response.raise_for_status()
        playlist = response.json().get("playlist", [])

        if not playlist:
            info("No tracks found in the playlist / album.")
            return

        parsed_tracks = parse_tracks(playlist)

        max_tracks = None
        if config and "lastfm" in config:
            max_tracks = config["lastfm"].get("max_tracks")
        
        if max_tracks and len(parsed_tracks) > max_tracks:
            info(f"Limiting to {max_tracks} tracks (found {len(parsed_tracks)})")
            parsed_tracks = parsed_tracks[:max_tracks]

        info(f"Fetched: {len(parsed_tracks)} tracks")
        
        # Cache library once at the start
        try:
            library_cache = client.listallinfo()
            info(f"Library cached: {len(library_cache)} items")
        except Exception as e:
            warning(f"Could not cache library: {e}")
            library_cache = []
        
        for artist, title, playlink_id in parsed_tracks:
            song_name = f"{artist} - {title}"
            
            # Check if track exists in library cache and get its file path
            file_path = is_track_in_library(artist, title, library_cache)
            if file_path:
                # Queue using the actual file path from library
                try:
                    client.add(file_path)
                    info(f"Queued: {song_name}")
                except Exception as e:
                    warning(f"Found in library but couldn't queue '{song_name}': {e}")
                    download_song(artist, title, music_folder, ydl_config, playlink_id)
            else:
                download_song(artist, title, music_folder, ydl_config, playlink_id)

    except RequestException as e:
        log_error(f"Can't fetch data from LastFM: {e}")


def parse_tracks(playlist):
    parsed_tracks = []
    for track in playlist:
        try:
            artist = track["artists"][0].get("name")
            title = track.get("name")
            playlink_id = track["_playlinks"][0].get("id")
            if artist and title and playlink_id:
                parsed_tracks.append((artist, title, playlink_id))
            else:
                warning(f"Incomplete track data: {track}")
        except (IndexError, KeyError) as e:
            warning(f"Error parsing track data: {e}")

    return parsed_tracks


def is_track_in_library(artist, title, library_cache=None):
    """Check if track exists in library and return its file path if found
    
    Returns:
        str or None: File path if found in library, None otherwise
    """
    if library_cache is None:
        return None
    
    for song in library_cache:
        if "artist" in song and "title" in song and "file" in song:
            if song["artist"] == artist and song["title"] == title:
                return song["file"]
    
    return None


def queue_song(song, check_only=False):
    """Queue a song or just check if it can be queued
    
    Args:
        song: Song name in format "Artist - Title"
        check_only: If True, only check if file exists without queuing
    
    Returns:
        bool: True if song exists and can be queued, False otherwise
    """
    try:
        client.update("dl")
        sleep(0.1)
        
        if check_only:
            # Just check if the file exists in MPD's database
            try:
                result = client.search("filename", f"dl/{song}.opus")
                return len(result) > 0
            except:
                return False
        
        client.add(f"dl/{song}.opus")
        info(f"Queued: {song}")
        return True
    except Exception as e:
        # Only log if we were actually trying to queue (not just checking)
        if not check_only:
            warning(f"Could not queue '{song}': {e}")
        return False


def download_song(
    artist, title, music_folder, ydl_config, playlink_id=None, return_success=False
):
    """
    Download a song using yt-dlp and queue it in MPD.

    Args:
        artist: Artist name
        title: Song title
        music_folder: Folder to download to
        ydl_config: yt-dlp configuration
        playlink_id: YouTube video ID (if None, will search YouTube)
        return_success: If True, returns success boolean instead of just logging

    Returns:
        bool: Success status if return_success=True, otherwise None
    """
    song = f"{artist} - {title}"

    # Progress bar setup
    pbar = None
    
    def progress_hook(d):
        nonlocal pbar
        if d['status'] == 'downloading':
            if pbar is None:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                pbar = tqdm(total=total, unit='B', unit_scale=True, desc=f"⬇ {song[:50]}", leave=False)
            downloaded = d.get('downloaded_bytes', 0)
            if pbar.total and downloaded <= pbar.total:
                pbar.n = downloaded
                pbar.refresh()
        elif d['status'] == 'finished':
            if pbar:
                pbar.close()
                pbar = None

    # Determine download URL/search
    if playlink_id:
        url_or_search = f"https://www.youtube.com/watch?v={playlink_id}"
        ydl_opts = {**ydl_config}
    else:
        url_or_search = f"{artist} {title}"
        ydl_opts = {**ydl_config, "default_search": "ytsearch1:"}

    ydl_opts.update(
        {
            "postprocessor_args": [
                "-metadata",
                f"title={title}",
                "-metadata",
                f"artist={artist}",
            ],
            "outtmpl": path.join(music_folder, f"{artist} - {title}"),
            "no_warnings": True,
            "ignoreerrors": False,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_color": True,
        }
    )

    try:
        # Temporarily redirect stderr to suppress yt-dlp error messages
        stderr_fd = stderr.fileno()
        old_stderr = dup(stderr_fd)
        devnull_fd = os_open(devnull, O_WRONLY)
        
        try:
            dup2(devnull_fd, stderr_fd)
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_or_search])
        finally:
            # Restore stderr
            dup2(old_stderr, stderr_fd)
            makedirs  # Keep import
        
        # Ensure progress bar is closed
        if pbar:
            pbar.close()

        # Queue the song
        queue_success = queue_song(song)

        if return_success:
            if queue_success:
                info(f"Downloaded and queued: {song}")
                return True
            else:
                warning(f"Downloaded but failed to queue: {song}")
                return False
        else:
            pass

    except Exception as e:
        # Extract just the core error message, skip yt-dlp prefix
        error_msg = str(e)
        if error_msg.startswith("ERROR: "):
            error_msg = error_msg[7:]  # Remove "ERROR: " prefix
        
        if return_success:
            warning(f"Could not download '{song}': {error_msg}")
            return False
        else:
            error(f"Could not download song '{song}': {error_msg}")

    return None if not return_success else False


def log_error(message):
    error(message)


def print_version_and_exit():
    try:
        ver = metadata.version("jukebox-fm")
        print(ver)
        exit(0)
    except Exception:
        try:
            here = path.dirname(path.dirname(path.dirname(__file__)))
            pyproject = path.join(here, "pyproject.toml")
            if path.exists(pyproject):
                with open(pyproject, "r") as f:
                    for line in f:
                        if line.strip().startswith("version"):
                            parts = line.split("=", 1)
                            if len(parts) == 2:
                                ver = parts[1].strip().strip('"').strip("'")
                                print(ver)
                                exit(0)
        except Exception:
            pass
    print("unknown")
    exit(0)


if __name__ == "__main__":
    main()
