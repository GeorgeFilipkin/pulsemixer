# pulsemixer
cli and curses mixer for pulseaudio

#### Requirements:
- `Python` >= 3
- `Pulseaudio` >= ?

No dbus, no additional pulseaudio configuration is required.

#### Usage:
```
Usage of pulsemixer:
  -h, --help               show this help message and exit
  -v, --version            print version
  -l, --list               list everything
  --list-sources           list sources
  --list-sinks             list sinks
  --id ID                  specify ID. If no ID specified - default sink is used
  --set-volume n           set volume for ID
  --set-volume-all n:n     set volume for ID (for every channel)
  --change-volume +-n      change volume for ID
  --get-mute               get mute for ID
  --toggle-mute            toggle mute for ID
  --get-volume             get volume for ID
  --mute                   mute ID
  --unmute                 unmute ID
```
It is possible to repeat arguments:
```
pulsemixer --get-volume --change-volume +5 --get-volume
65 65
70 70
```

If no arguments given - interactive mode is used. Which looks like this:
![Image of whatever](../img//scrn.png?raw=true)

And has the following controls:
```
  h/j/k/l                       navigation, volume change
  arrows                        navigation, volume change
  H/L, Shift+Left/Shift+Right   change volume by 10
  1/2/3/4/5/6/7/8/9/0           set volume to 10%/20%/30%/40%/50%/60%/70%/80%/90%/100%
  m                             mute/unmute
  Space                         lock/unlock channels together
  Enter                         context menu
  F1/F2                         change modes
  Tab                           go to next mode
  ?                             show help
  q/Esc/^C                      quit
```

Via context menu it is possible to `set-default-sink`, `set-default-source`, `move-sink-input`, `move-source-output`, `suspend-sink`, `suspend-source`, `set-sink-port`, `set-source-port`. See `man pactl` for details on these features.

## License
This project is licensed under the terms of the MIT license
