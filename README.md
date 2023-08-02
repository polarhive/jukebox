# jukebox

Play LastFM recommendations on linux: using [`mpd(1)`](https://man.archlinux.org/man/mpd.1), [`yt-dlp(1)`](https://man.archlinux.org/man/yt-dlp.1) and [`bash(1)`](https://man.archlinux.org/man/bash.1)

## usage

``./jukebox``
```
Options:
  -u: Play user's lastfm mix [default]
  -a <artist>: Artist name
  -g <genre>: Genre name
  -s <song name by artist>: Search a song
  -y: Use yt-music tags for songs [-u mode only]
  -h: Display this help message
```

## setup

- edit the script to use: your LastFM username
- choose to play:
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
- [ ] voice-recognition/search via vosk [ref:](https://piped.video/watch?v=zXEvKJl_krY) bugswriter's video

### prerequisites

- `mpd`, `yt-dlp`, `jq` and optionally `mpdscribble` (to scrobble to LastFM)
- run `systemctl --user enable --now mpd mpdscribble` at least once before running jukebox
- read: [foss-music-setup](https://polarhive.net/blog/foss-music-setup) or use my [dotfiles](https://polarhive.net/dots)

---
This repo is hosted on [Codeberg](https://polarhive.net/jukebox) & mirrored to [GitHub](https://polarhive.net/github) for traffic.

[![license: GPLv3 or Later](https://polarhive.net/assets/badges/gpl-3.svg)](https://www.gnu.org/licenses/gpl-3.0.txt)

