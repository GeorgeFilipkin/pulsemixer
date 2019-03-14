# pulsemixer
cli and curses mixer for pulseaudio

### Requirements
- `Python` >= 3
- `PulseAudio` >= 1.0

## Installation

Pulsemixer is a self-sufficient single-file python script that doesn't require any extra libraries. So you can simply download [pulsemixer](https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/master/pulsemixer) manually, do `chmod +x ./pulsemixer` and put it anywhere you want.

Below are some more convenient ways to install pulsemixer:

##### pip

```
pip3 install pulsemixer
```

##### curl

```sh
curl https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/master/pulsemixer > pulsemixer && chmod +x ./pulsemixer
```

## CLI usage
```
Usage of pulsemixer:
  -h, --help            show this help message and exit
  -v, --version         print version
  -l, --list            list everything
  --list-sources        list sources
  --list-sinks          list sinks
  --id ID               specify ID. If no ID specified - default sink is used
  --set-volume n        set volume for ID
  --set-volume-all n:n  set volume for ID (for every channel)
  --change-volume +-n   change volume for ID
  --max-volume n        set volume to n if volume is higher than n
  --get-mute            get mute for ID
  --toggle-mute         toggle mute for ID
  --get-volume          get volume for ID
  --mute                mute ID
  --unmute              unmute ID
  --server              choose the server to connect to
  --color n             0 no color, 1 color currently selected, 2 full-color (default)
  --no-mouse            disable mouse support
  --create-config       generate configuration file
```
It is possible to repeat arguments:
```
pulsemixer --get-volume --change-volume +5 --get-volume
65 65
70 70
```
And chain commands with a single call. For example you could do this:
```
pulsemixer --id 470 --get-volume --id 2 --get-volume --change-volume +5 --get-volume
90 90
100 100
105 105
```

## Interactive mode
Interactive mode is used when no arguments were given (except `--color` and `--server`)

![Image of 1](https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/img/1.png)
![Image of 2](https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/img/2.png)

Interactive controls:
```
 j k   ↑ ↓               Navigation
 h l   ← →               Change volume
 H L   Shift←  Shift→    Change volume by 10
 1 2 3 .. 8 9 0          Set volume to 10%-100%
 m                       Mute/Unmute
 Space                   Lock/Unlock channels
 Enter                   Context menu
 F1 F2 F3                Change modes
 Tab   Shift Tab         Next/Previous mode
 Mouse click             Select device or mode
 Mouse wheel             Volume change
 Esc q                   Quit

```

Via context menu it is possible to `set-default-sink`, `set-default-source`, `move-sink-input`, `move-source-output`, `suspend-sink`, `suspend-source`, `set-sink-port`, `set-source-port`, `kill-client`, `kill-sink-input`, `kill-source-output`, `set-card-profile`. See `man pactl` for details on these features.

## Configuration
Optional.  
The config file will not be created automatically. Do `pulsemixer --create-config` or copy-paste it from here.

```ini
;; Goes into ~/.config/pulsemixer.cfg, $XDG_CONFIG_HOME respected
;; Everything that starts with "#" or ";" is a comment
;; For the option to take effect simply uncomment it

[general]
step = 1
step-big = 10
; server = 

[keys]
;; To bind "special keys" such as arrows see "Key constant" table in
;; https://docs.python.org/3/library/curses.html#constants
; up        = k, KEY_UP, KEY_PPAGE
; down      = j, KEY_DOWN, KEY_NPAGE
; left      = h, KEY_LEFT
; right     = l, KEY_RIGHT
; left-big  = H, KEY_SLEFT
; right-big = L, KEY_SRIGHT
; top       = g, KEY_HOME
; bottom    = G, KEY_END
; mode1     = KEY_F1
; mode2     = KEY_F2
; mode3     = KEY_F3
; next-mode = KEY_TAB
; prev-mode = KEY_BTAB
; mute      = m
; lock      = ' '  ; 'space', quotes are stripped
; quit      = q, KEY_ESC

[ui]
; hide-unavailable-profiles = no
; hide-unavailable-ports = no
; color = 2    ; same as --color, 0 no color, 1 color currently selected, 2 full-color
; mouse = yes

[style]
;; Pulsemixer will use these characters to draw interface
;; Single characters only
;; Keep in mind that vte-based terminals might have problems displaying wide unicode symbols
;;      https://bugzilla.gnome.org/show_bug.cgi?id=772890
; bar-top-left       = ┌
; bar-left-mono      = ╶
; bar-top-right      = ┐
; bar-right-mono     = ╴
; bar-bottom-left    = └
; bar-bottom-right   = ┘
; bar-on             = ▮
; bar-off            = -
; arrow              = ' '
; arrow-focused      = ─
; arrow-locked       = ─
; default-stream     = *
; info-locked        = L
; info-unlocked      = U
; info-muted         = M  ; 🔇
; info-unmuted       = M  ; 🔉
```

The old environment variable `PULSEMIXER_BAR_STYLE` is still supported.  
To change the volume bar's appearance in (e.g.) zsh without creating the config file:
```bash
export PULSEMIXER_BAR_STYLE="╭╶╮╴╰╯◆· ──"
```
