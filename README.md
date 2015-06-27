# pulsemixer
cli and curses mixer for pulseaudio

#### Requirements:
* Python >= 3
* Pulseaudio >= ?

#### Usage:
```
usage: pulsemixer [-h] [-l] [--list-sources] [--list-sinks] [--id ID]
                  [--set-volume n] [--set-volume-all [n [n ...]]]
                  [--change-volume +-n] [--get-mute] [--toggle-mute]
                  [--get-volume] [--mute] [--unmute]

optional arguments:
  -h, --help                    show this help message and exit
  -l, --list                    list everything
  --list-sources                list sources
  --list-sinks                  list sinks
  --id ID                       specify ID. If no ID specified - master sink is used
  --set-volume n                set volume for ID
  --set-volume-all [n [n ...]]  set volume for ID (for every channel)
  --change-volume +-n           change volume for ID
  --get-mute                    get mute for ID
  --toggle-mute                 toggle mute for ID
  --get-volume                  get volume for ID
  --mute                        mute ID
```


If no options are specified - interactive mode is used. Which looks like this:
![Image of whatever](../img//scrn.png?raw=true)

And has the following controls:
```
h/j/k/l - left, down, up, right. Or you can use arrows, yes.
M - mute/unmute
Space - lock/unlock channels together
Q/Esc/^C - quit
```
