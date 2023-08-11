# MPD Snapcast Stream

> Stream your songs from your webserver using MPD, [snapcast](https://github.com/badaix/snapcast/) & [Tailscale](https://tailscale.com).

```
Network:
[mpd ⟶ snapcast_server (on nimbu)] <~tailscale~> [snapcast_client (on vince): nimbu]

Hosts:
• nimbu: my remote machine
• cider: my local machine (linux)
• vince: my local machine (android)
```

## setup:

On your **remote** machine: `nvim ~/.config/mpd/mpd.conf`

#### 1. Add this block:

```
audio_output {
    type            "fifo"
    name            "snapcast"
    path            "/tmp/snapfifo"
    format          "48000:16:2"
    mixer_type      "software"
}
```

#### 2. Restart MPD:

```
systemctl --user restart mpd
```

#### 3. Set up Tailscale:

```
curl -fsSL https://tailscale.com/install.sh | sh
```

#### 4. Open up ports

```
sudo ufw allow 1704/tcp
sudo ufw allow 1705/tcp
sudo ufw allow 1780/tcp
```

#### 5. Set up Snapcast

```
# install snapcast
https://github.com/badaix/snapcast/blob/develop/doc/install.md

# start the snapcast service
sudo systemctl restart snapserver
```

---
#### On your **local** machine:

Connect to your snapcast_server

- On Android: Use the snapcast app from [F-Droid](https://f-droid.org/en/packages/de.badaix.snapcast/)
- Tap settings. I've to set `nimbu` as my hostname
- If you don't want to install an app: Visit http://nimbu:1780 for a web-interface!

> Make sure tailscale is up and running!

