# pulsemixer
cli and curses mixer for pulseaudio

### Requirements:
- `Python` >= 3
- `PulseAudio` >= 1.0

## Installation:

Pulsemixer is a self-sufficient single-file python script that doesn't require any extra libraries. So you can simply download [pulsemixer](https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/master/pulsemixer) manually, do `chmod +x ./pulsemixer` and put it anywhere you want.

Below are some more convenient ways to install pulsemixer:

##### Pip:  

```
pip3 install pulsemixer
```

##### curl:

```sh
curl https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/master/pulsemixer > pulsemixer && chmod +x ./pulsemixer
```

## CLI usage:
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
  --get-mute            get mute for ID
  --toggle-mute         toggle mute for ID
  --get-volume          get volume for ID
  --mute                mute ID
  --unmute              unmute ID
  --server              choose the server to connect to
  --color n             0 no color, 1 color currently selected, 2 full-color (default)
  --no-mouse            disable mouse support
```
It is possible to repeat arguments:
```
pulsemixer --get-volume --change-volume +5 --get-volume
65 65
70 70
```
**Note on id:** `--id` must be specified before the set/get/mute command, i.e. `pulsemixer --id 470 --get-volume`. If `--id` isn't specified of specified after the command, then that command will use default sink.

It is not the most common cli behavior (and may be changed in the future), but it was done to avoid consecutive calls to pulsemixer, to chain commands with a single call. For example you could do this:
```
pulsemixer --id 470 --get-volume --id 2 --get-volume --change-volume +5 --get-volume
90 90
100 100
105 105
```

## Interactive mode:
Interactive mode is used when no arguments were given (except `--color` and `--server`)

![Image of 1](https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/img/1.png)
![Image of 2](https://raw.githubusercontent.com/GeorgeFilipkin/pulsemixer/img/2.png)

Interactive controls:
```
  h/j/k/l, arrows               navigation, volume change
  PgUp/PgDn                     navigation
  Home/End                      select first/last device
  H/L, Shift+Left/Shift+Right   change volume by 10
  1/2/3/4/5/6/7/8/9/0           set volume to 10%-100%
  m                             mute/unmute
  Space                         lock/unlock channels together
  Enter                         context menu
  F1/F2/F3                      change modes
  Tab                           go to next mode
  Mouse left click              select device or mode
  Mouse wheel                   volume change
  q/Esc/^C                      quit
```

Via context menu it is possible to `set-default-sink`, `set-default-source`, `move-sink-input`, `move-source-output`, `suspend-sink`, `suspend-source`, `set-sink-port`, `set-source-port`, `kill-client`, `kill-sink-input`, `kill-source-output`, `set-card-profile`. See `man pactl` for details on these features.

## Customizing:
The volume bar's appearance can be changed with the environment variable PULSEMIXER_BAR_STYLE.

The bar characters are defined as:
```
PULSEMIXER_BAR_STYLE="xxxxxxxxxxx"
                      |||||||||||
top left corner      -+||||||||||
left side (mono)     --+|||||||||
top right corner     ---+||||||||
right side (mono)    ----+|||||||
bottom left corner   -----+||||||
bottom right corner  ------+|||||
bar segment (on)     -------+||||
bar segment (off)    --------+|||
channel (deselected) ---------+||
channel (selected)   ----------+|
channel (linked)     -----------+
```
To set the bar style in (e.g.) zsh:
```
export PULSEMIXER_BAR_STYLE="┌╶┐╴└┘♥  ◆┆"
```

## License
This project is licensed under the terms of the MIT license
