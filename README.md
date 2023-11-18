# jukebox

Play LastFM music recommendations using: [`mpd(1)`](https://man.archlinux.org/man/mpd.1), [`yt-dlp(1)`](https://man.archlinux.org/man/yt-dlp.1) and [`bash(1)`](https://man.archlinux.org/man/bash.1)

```
jukebox -h
  -a: <artist name>
  -g: <genre name>
  -s: <song name>
  -u: <lastfm: username>
  -m: <lastfm: mix | recommended | library>
  -p: <lastfm: playlist url>
  -l: vosk: search songs with your voice
  -y: use ytmusic tags for songs
  -c: top charts in your region (setup your api_key)
```
---
## usage: [demo](https://www.youtube.com/watch?v=k2hNvjDdBRk)

```
jukebox -g "rap"
jukebox -m "library"
jukebox -a "Drake"
jukebox -s "Never Gonna Give You Up"
```

## setup:

```
git clone https://codeberg.org/polarhive/jukebox
cd jukebox
```

- Open the script in a text editor: `nvim jukebox`
- Set your LastFM username: [default: polarhive]
- Set your preferred mode: [default: mix]
  * recommended: Listen to recommended music from LastFM
  * library: Listen to music you’ve scrobbled before
  * mix: Listen to music you’ve scrobbled before + recommendations from LastFM
- Install: `mpd`, `yt-dlp`, `jq` and optionally `mpdscribble` (to scrobble to LastFM)
- Activate services: `systemctl --user enable --now mpd mpdscribble` before running jukebox

## extensions:

- Read my blog [/post](https://polarhive.net/blog/jukebox) or use my [/dotfiles](https://polarhive.net/dots) for my exact setup
- [charts](charts): requires an [`$api_key`](https://www.last.fm/api/account/create)
- [listen](listen): `pip install vosk google-speech` and `pacman -S sox`
- [docs/stream](docs/snapcast.md): Stream songs to your other devices like a phone, laptop or speaker
- [docs/phone](docs/phone.md): Copy your current-playlist to your phone: using `rsync` & `adb` for offline-playback

---
This repo is hosted on [Codeberg](https://polarhive.net/jukebox) & mirrored to [GitHub](https://polarhive.net/github) for traffic.

[![license: GPLv3 or Later](https://polarhive.net/assets/badges/gpl-3.svg)](https://www.gnu.org/licenses/gpl-3.0.txt)

