# jukebox

Play LastFM recommendations on linux: using [`mpd(1)`](https://man.archlinux.org/man/mpd.1), [`yt-dlp(1)`](https://man.archlinux.org/man/yt-dlp.1) and [`bash(1)`](https://man.archlinux.org/man/bash.1)

## usage: [demo](https://polarhive.net/videos/jukebox-demo-lastfm-linux)

`./jukebox`

```
jukebox -h
  -a: <artist name>
  -g: <genre name>
  -s: <song name>

  -u: <lastfm: username>
  -m: <lastfm: mix | recommended | library>

  -l: vosk: uses your mic to search songs
  -y: use ytmusic tags for songs
  -c: top charts in your region (setup your api_key)

```

## setup:

- edit the script to: use your LastFM `$username`
- choose between:
  * recommended: Listen to recommended music from Last.fm
  * library: Listen to music you’ve scrobbled before
  * mix: Listen to a mix of music you’ve scrobbled before and recommendations from Last.fm

---
## todo/bugs

- [x] sanity-check title/artist tags before scrobbling
- [x] figure your how to `mpc add` songs properly
- [x] make the script interactive
- [x] fast(er)? yt-dlp fetches
- [x] custom artist/album search
- [x] global charts
- [x] voice-recognition/search via vosk [ref:](https://piped.video/watch?v=zXEvKJl_krY) bugswriter's video

### prerequisites:

- `mpd`, `yt-dlp`, `jq` and optionally `mpdscribble` (to scrobble to LastFM)
- run `systemctl --user enable --now mpd mpdscribble` at least once before running jukebox
- read: [foss-music-setup](https://polarhive.net/blog/foss-music-setup) or use my [dotfiles](https://polarhive.net/dots)

#### extra:

- [charts](charts): LastFM [`$api_key`](https://www.last.fm/api/account/create)
- [listen](listen): `pip install vosk google-speech` & `pacman -S sox`

---
This repo is hosted on [Codeberg](https://polarhive.net/jukebox) & mirrored to [GitHub](https://polarhive.net/github) for traffic.

[![license: GPLv3 or Later](https://polarhive.net/assets/badges/gpl-3.svg)](https://www.gnu.org/licenses/gpl-3.0.txt)

