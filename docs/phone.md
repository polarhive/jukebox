# Phone

> Copy your current mpd-playlist to your phone: for offline playback and scrobbling on the go!

```
• cider: my local machine (laptop)
• vince: my remote machine (android)
```

## setup

### cider:

```
pacman -S android-sdk-platform-tools rsync
reboot
```

### vince:

- `Settings -> About Phone -> Keep tapping build number`
- `Settings -> System -> Developer Options -> enable Android Debugging`
- Plug in your phone to your laptop via a cable
- On your laptop run: `adb devices` to check if adb is up and running?
- If prompted for USB debugging authorization: tap yes

### On your laptop:

> Download [pScrobbler](https://github.com/kawaiiDango/pScrobbler/releases/latest) (like mpdscribble; but for Android)

```
adb install ~/Downloads/pScrobbler-release.apk
```

## Sync

> Now, run `psync` on your laptop

```
sh ~/jukebox/psync
```

- Launch pScrobbler on your phone; finish the setup (if you wish to scrobble songs)
- Open your `Music` folder -> tap on `songs.m3u` to play your songs
