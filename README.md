# jukebox

Play LastFM music recommendations using: [`mpd(1)`](https://man.archlinux.org/man/mpd.1), [`yt-dlp(1)`](https://man.archlinux.org/man/yt-dlp.1) and [`bash(1)`](https://man.archlinux.org/man/bash.1)

```
jukebox -g "rap"
jukebox -m "library"
jukebox -a "Drake"
jukebox -s "Never Gonna Give You Up"
```

## setup

```
git clone https://codeberg.org/polarhive/jukebox
```

> Edit the script: `nvim jukebox`

- Set your LastFM **username**: [default: polarhive]
- Set a preferred queue **mode**: [default: mix]
  - recommended: discover new music based on your LastFM profile
  - library: music you've scrobbled before
  - mix: music you've scrobbled before + recommendations from LastFM
- Install: `mpd`, `yt-dlp`, `jq` and optionally `mpdscribble` (to scrobble to LastFM)
- Activate units: `systemctl --user enable --now mpd mpdscribble` before running jukebox

## docs/extensions

- [docs/stream](docs/snapcast.md): Stream songs to your other devices like a phone, laptop or speaker
- [docs/phone](docs/phone.md): Sync your playlist queue to your phone: using `rsync` & `adb` for offline-playback
- [charts](charts): requires an [`$api_key`](https://www.last.fm/api/account/create)
- [listen](listen): `pip install vosk google-speech` and `pacman -S sox`
- Here's my [/post](https://polarhive.net/blog/jukebox) about jukebox.
- Use my [/dotfiles](https://polarhive.net/dots) for reference.

---
This repo is hosted on [Codeberg](https://codeberg.org/polarhive/jukebox) & mirrored to [GitHub](https://polarhive.net/github) for traffic.

[![GPL enforced badge](https://img.shields.io/badge/GPL-enforced-blue.svg "This project enforces the GPL.")](https://gplenforced.org)
