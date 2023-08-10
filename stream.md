# MPD HTTP Stream

> Stream your songs from your webserver using MPD & [Tailscale](https://tailscale.com).

```
Network:
[nimbu mpd:8000] <~tailscale~> [cider: mpv 'nimbu:8000']

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
    type            "httpd"
    name            "stream"
    port            "8000"
    format          "48000:16:1"
    always_on       "yes"                   # prevent MPD from disconnecting all listeners when playback is stopped
    tags            "yes"                   # httpd supports sending tags to listening streams
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

#### 4. Copy your remote machine's IPv6 address:

```
tailscale ip -6
```
---
#### On your **local** machine:

Connect to your MPD server:

```
export MPD_HOST='YOUR_IPv6_ADDRESS'
mpc play
```

Make sure tailscale is up and running!

> Replace `YOUR_IPv6_ADDRESS` with your remote machine's IPv6 address.

