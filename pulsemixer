#!/usr/bin/env python3
'''Usage of pulsemixer:
  -h, --help            show this help message and exit
  -v, --version         print version
  -l, --list            list everything
  --list-sources        list sources
  --list-sinks          list sinks
  --id ID               specify ID, default sink is used if no ID specified
  --get-volume          get volume for ID
  --set-volume n        set volume for ID
  --set-volume-all n:n  set volume for ID, for every channel
  --change-volume +-n   change volume for ID
  --max-volume n        set volume to n if volume is higher than n
  --get-mute            get mute for ID
  --mute                mute ID
  --unmute              unmute ID
  --toggle-mute         toggle mute for ID
  --server              choose the server to connect to
  --color n             0 no color, 1 color currently selected, 2 full-color
  --no-mouse            disable mouse support
  --create-config       generate configuration file'''

VERSION = '1.5.1'

import curses
import functools
import getopt
import operator
import os
import re
import signal
import sys
import threading
import traceback
from collections import OrderedDict
from configparser import ConfigParser
from ctypes import *
from itertools import takewhile
from pprint import pprint
from select import select
from shutil import get_terminal_size
from textwrap import dedent
from time import sleep
from unicodedata import east_asian_width

#########################################################################################
# v bindings

try:
    DLL = CDLL("libpulse.so.0")
except Exception as e:
    sys.exit(e)

PA_VOLUME_NORM = 65536
PA_CHANNELS_MAX = 32
PA_USEC_T = c_uint64
PA_CONTEXT_READY = 4
PA_CONTEXT_FAILED = 5
PA_SUBSCRIPTION_MASK_ALL = 0x02ff


class Struct(Structure): pass
PA_PROPLIST = PA_OPERATION = PA_CONTEXT = PA_THREADED_MAINLOOP = PA_MAINLOOP_API = Struct


class PA_SAMPLE_SPEC(Structure):
    _fields_ = [
        ("format",      c_int),
        ("rate",        c_uint32),
        ("channels",    c_uint32)
    ]


class PA_CHANNEL_MAP(Structure):
    _fields_ = [
        ("channels",    c_uint8),
        ("map",         c_int * PA_CHANNELS_MAX)
    ]


class PA_CVOLUME(Structure):
    _fields_ = [
        ("channels",    c_uint8),
        ("values",      c_uint32 * PA_CHANNELS_MAX)
    ]


class PA_PORT_INFO(Structure):
    _fields_ = [
        ('name',        c_char_p),
        ('description', c_char_p),
        ('priority',    c_uint32),
        ("available",   c_int),
    ]


class PA_SINK_INPUT_INFO(Structure):
    _fields_ = [
        ("index",           c_uint32),
        ("name",            c_char_p),
        ("owner_module",    c_uint32),
        ("client",          c_uint32),
        ("sink",            c_uint32),
        ("sample_spec",     PA_SAMPLE_SPEC),
        ("channel_map",     PA_CHANNEL_MAP),
        ("volume",          PA_CVOLUME),
        ("buffer_usec",     PA_USEC_T),
        ("sink_usec",       PA_USEC_T),
        ("resample_method", c_char_p),
        ("driver",          c_char_p),
        ("mute",            c_int),
        ("proplist",        POINTER(PA_PROPLIST))
    ]


class PA_SINK_INFO(Structure):
    _fields_ = [
        ("name",                c_char_p),
        ("index",               c_uint32),
        ("description",         c_char_p),
        ("sample_spec",         PA_SAMPLE_SPEC),
        ("channel_map",         PA_CHANNEL_MAP),
        ("owner_module",        c_uint32),
        ("volume",              PA_CVOLUME),
        ("mute",                c_int),
        ("monitor_source",      c_uint32),
        ("monitor_source_name", c_char_p),
        ("latency",             PA_USEC_T),
        ("driver",              c_char_p),
        ("flags",               c_int),
        ("proplist",            POINTER(PA_PROPLIST)),
        ("configured_latency",  PA_USEC_T),
        ('base_volume',         c_int),
        ('state',               c_int),
        ('n_volume_steps',      c_int),
        ('card',                c_uint32),
        ('n_ports',             c_uint32),
        ('ports',               POINTER(POINTER(PA_PORT_INFO))),
        ('active_port',         POINTER(PA_PORT_INFO))
    ]


class PA_SOURCE_OUTPUT_INFO(Structure):
    _fields_ = [
        ("index",           c_uint32),
        ("name",            c_char_p),
        ("owner_module",    c_uint32),
        ("client",          c_uint32),
        ("source",          c_uint32),
        ("sample_spec",     PA_SAMPLE_SPEC),
        ("channel_map",     PA_CHANNEL_MAP),
        ("buffer_usec",     PA_USEC_T),
        ("source_usec",     PA_USEC_T),
        ("resample_method", c_char_p),
        ("driver",          c_char_p),
        ("proplist",        POINTER(PA_PROPLIST)),
        ("corked",          c_int),
        ("volume",          PA_CVOLUME),
        ("mute",            c_int),
    ]


class PA_SOURCE_INFO(Structure):
    _fields_ = [
        ("name",                 c_char_p),
        ("index",                c_uint32),
        ("description",          c_char_p),
        ("sample_spec",          PA_SAMPLE_SPEC),
        ("channel_map",          PA_CHANNEL_MAP),
        ("owner_module",         c_uint32),
        ("volume",               PA_CVOLUME),
        ("mute",                 c_int),
        ("monitor_of_sink",      c_uint32),
        ("monitor_of_sink_name", c_char_p),
        ("latency",              PA_USEC_T),
        ("driver",               c_char_p),
        ("flags",                c_int),
        ("proplist",             POINTER(PA_PROPLIST)),
        ("configured_latency",   PA_USEC_T),
        ('base_volume',          c_int),
        ('state',                c_int),
        ('n_volume_steps',       c_int),
        ('card',                 c_uint32),
        ('n_ports',              c_uint32),
        ('ports',                POINTER(POINTER(PA_PORT_INFO))),
        ('active_port',          POINTER(PA_PORT_INFO))
    ]


class PA_CLIENT_INFO(Structure):
    _fields_ = [
        ("index",        c_uint32),
        ("name",         c_char_p),
        ("owner_module", c_uint32),
        ("driver",       c_char_p)
    ]


class PA_CARD_PROFILE_INFO(Structure):
    _fields_ = [
        ('name',        c_char_p),
        ('description', c_char_p),
        ('n_sinks',     c_uint32),
        ('n_sources',   c_uint32),
        ('priority',    c_uint32),
    ]


class PA_CARD_PROFILE_INFO2(Structure):
    _fields_ = PA_CARD_PROFILE_INFO._fields_ + [('available',   c_int)]


class PA_CARD_INFO(Structure):
    _fields_ = [
        ('index',           c_uint32),
        ('name',            c_char_p),
        ('owner_module',    c_uint32),
        ('driver',          c_char_p),
        ('n_profiles',      c_uint32),
        ('profiles',        POINTER(PA_CARD_PROFILE_INFO)),
        ('active_profile',  POINTER(PA_CARD_PROFILE_INFO)),
        ('proplist',        POINTER(PA_PROPLIST)),
        ('n_ports',         c_uint32),
        ('ports',           POINTER(POINTER(c_void_p))),
        ('profiles2',       POINTER(POINTER(PA_CARD_PROFILE_INFO2))),
        ('active_profile2', POINTER(PA_CARD_PROFILE_INFO2))
    ]


class PA_SERVER_INFO(Structure):
    _fields_ = [
        ('user_name',           c_char_p),
        ('host_name',           c_char_p),
        ('server_version',      c_char_p),
        ('server_name',         c_char_p),
        ('sample_spec',         PA_SAMPLE_SPEC),
        ('default_sink_name',   c_char_p),
        ('default_source_name', c_char_p),
    ]


PA_STATE_CB_T              = CFUNCTYPE(c_int, POINTER(PA_CONTEXT), c_void_p)
PA_CLIENT_INFO_CB_T        = CFUNCTYPE(c_void_p, POINTER(PA_CONTEXT), POINTER(PA_CLIENT_INFO), c_int, c_void_p)
PA_SINK_INPUT_INFO_CB_T    = CFUNCTYPE(c_int, POINTER(PA_CONTEXT), POINTER(PA_SINK_INPUT_INFO), c_int, c_void_p)
PA_SINK_INFO_CB_T          = CFUNCTYPE(c_int, POINTER(PA_CONTEXT), POINTER(PA_SINK_INFO), c_int, c_void_p)
PA_SOURCE_OUTPUT_INFO_CB_T = CFUNCTYPE(c_int, POINTER(PA_CONTEXT), POINTER(PA_SOURCE_OUTPUT_INFO), c_int, c_void_p)
PA_SOURCE_INFO_CB_T        = CFUNCTYPE(c_int, POINTER(PA_CONTEXT), POINTER(PA_SOURCE_INFO), c_int, c_void_p)
PA_CONTEXT_SUCCESS_CB_T    = CFUNCTYPE(c_void_p, POINTER(PA_CONTEXT), c_int, c_void_p)
PA_CARD_INFO_CB_T          = CFUNCTYPE(None, POINTER(PA_CONTEXT), POINTER(PA_CARD_INFO), c_int, c_void_p)
PA_SERVER_INFO_CB_T        = CFUNCTYPE(None, POINTER(PA_CONTEXT), POINTER(PA_SERVER_INFO), c_void_p)
PA_CONTEXT_SUBSCRIBE_CB_T  = CFUNCTYPE(c_void_p, POINTER(PA_CONTEXT), c_int, c_int, c_void_p)

pa_threaded_mainloop_new = DLL.pa_threaded_mainloop_new
pa_threaded_mainloop_new.restype = POINTER(PA_THREADED_MAINLOOP)
pa_threaded_mainloop_new.argtypes = []

pa_threaded_mainloop_free = DLL.pa_threaded_mainloop_free
pa_threaded_mainloop_free.restype = c_void_p
pa_threaded_mainloop_free.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_threaded_mainloop_start = DLL.pa_threaded_mainloop_start
pa_threaded_mainloop_start.restype = c_int
pa_threaded_mainloop_start.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_threaded_mainloop_stop = DLL.pa_threaded_mainloop_stop
pa_threaded_mainloop_stop.restype = None
pa_threaded_mainloop_stop.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_threaded_mainloop_lock = DLL.pa_threaded_mainloop_lock
pa_threaded_mainloop_lock.restype = None
pa_threaded_mainloop_lock.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_threaded_mainloop_unlock = DLL.pa_threaded_mainloop_unlock
pa_threaded_mainloop_unlock.restype = None
pa_threaded_mainloop_unlock.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_threaded_mainloop_wait = DLL.pa_threaded_mainloop_wait
pa_threaded_mainloop_wait.restype = None
pa_threaded_mainloop_wait.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_threaded_mainloop_signal = DLL.pa_threaded_mainloop_signal
pa_threaded_mainloop_signal.restype = None
pa_threaded_mainloop_signal.argtypes = [POINTER(PA_THREADED_MAINLOOP), c_int]

pa_threaded_mainloop_get_api = DLL.pa_threaded_mainloop_get_api
pa_threaded_mainloop_get_api.restype = POINTER(PA_MAINLOOP_API)
pa_threaded_mainloop_get_api.argtypes = [POINTER(PA_THREADED_MAINLOOP)]

pa_context_errno = DLL.pa_context_errno
pa_context_errno.restype = c_int
pa_context_errno.argtypes = [POINTER(PA_CONTEXT)]

pa_context_new_with_proplist = DLL.pa_context_new_with_proplist
pa_context_new_with_proplist.restype = POINTER(PA_CONTEXT)
pa_context_new_with_proplist.argtypes = [POINTER(PA_MAINLOOP_API), c_char_p, POINTER(PA_PROPLIST)]

pa_context_unref = DLL.pa_context_unref
pa_context_unref.restype = None
pa_context_unref.argtypes = [POINTER(PA_CONTEXT)]

pa_context_set_state_callback = DLL.pa_context_set_state_callback
pa_context_set_state_callback.restype = None
pa_context_set_state_callback.argtypes = [POINTER(PA_CONTEXT), PA_STATE_CB_T, c_void_p]

pa_context_connect = DLL.pa_context_connect
pa_context_connect.restype = c_int
pa_context_connect.argtypes = [POINTER(PA_CONTEXT), c_char_p, c_int, POINTER(c_int)]

pa_context_get_state = DLL.pa_context_get_state
pa_context_get_state.restype = c_int
pa_context_get_state.argtypes = [POINTER(PA_CONTEXT)]

pa_context_disconnect = DLL.pa_context_disconnect
pa_context_disconnect.restype = c_int
pa_context_disconnect.argtypes = [POINTER(PA_CONTEXT)]

pa_operation_unref = DLL.pa_operation_unref
pa_operation_unref.restype = None
pa_operation_unref.argtypes = [POINTER(PA_OPERATION)]

pa_context_subscribe = DLL.pa_context_subscribe
pa_context_subscribe.restype = POINTER(PA_OPERATION)
pa_context_subscribe.argtypes = [POINTER(PA_CONTEXT), c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_subscribe_callback = DLL.pa_context_set_subscribe_callback
pa_context_set_subscribe_callback.restype = None
pa_context_set_subscribe_callback.args = [POINTER(PA_CONTEXT), PA_CONTEXT_SUBSCRIBE_CB_T, c_void_p]

pa_proplist_new = DLL.pa_proplist_new
pa_proplist_new.restype = POINTER(PA_PROPLIST)

pa_proplist_sets = DLL.pa_proplist_sets
pa_proplist_sets.argtypes = [POINTER(PA_PROPLIST), c_char_p, c_char_p]

pa_proplist_gets = DLL.pa_proplist_gets
pa_proplist_gets.restype = c_char_p
pa_proplist_gets.argtypes = [POINTER(PA_PROPLIST), c_char_p]

pa_proplist_free = DLL.pa_proplist_free
pa_proplist_free.argtypes = [POINTER(PA_PROPLIST)]

pa_context_get_sink_input_info_list = DLL.pa_context_get_sink_input_info_list
pa_context_get_sink_input_info_list.restype = POINTER(PA_OPERATION)
pa_context_get_sink_input_info_list.argtypes = [POINTER(PA_CONTEXT), PA_SINK_INPUT_INFO_CB_T, c_void_p]

pa_context_get_sink_info_list = DLL.pa_context_get_sink_info_list
pa_context_get_sink_info_list.restype = POINTER(PA_OPERATION)
pa_context_get_sink_info_list.argtypes = [POINTER(PA_CONTEXT), PA_SINK_INFO_CB_T, c_void_p]

pa_context_set_sink_mute_by_index = DLL.pa_context_set_sink_mute_by_index
pa_context_set_sink_mute_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_sink_mute_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_suspend_sink_by_index = DLL.pa_context_suspend_sink_by_index
pa_context_suspend_sink_by_index.restype = POINTER(PA_OPERATION)
pa_context_suspend_sink_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_sink_port_by_index = DLL.pa_context_set_sink_port_by_index
pa_context_set_sink_port_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_sink_port_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_char_p, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_sink_input_mute = DLL.pa_context_set_sink_input_mute
pa_context_set_sink_input_mute.restype = POINTER(PA_OPERATION)
pa_context_set_sink_input_mute.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_sink_volume_by_index = DLL.pa_context_set_sink_volume_by_index
pa_context_set_sink_volume_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_sink_volume_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, POINTER(PA_CVOLUME), PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_sink_input_volume = DLL.pa_context_set_sink_input_volume
pa_context_set_sink_input_volume.restype = POINTER(PA_OPERATION)
pa_context_set_sink_input_volume.argtypes = [POINTER(PA_CONTEXT), c_uint32, POINTER(PA_CVOLUME), PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_move_sink_input_by_index = DLL.pa_context_move_sink_input_by_index
pa_context_move_sink_input_by_index.restype = POINTER(PA_OPERATION)
pa_context_move_sink_input_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_uint32, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_default_sink = DLL.pa_context_set_default_sink
pa_context_set_default_sink.restype = POINTER(PA_OPERATION)
pa_context_set_default_sink.argtypes = [POINTER(PA_CONTEXT), c_char_p, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_kill_sink_input = DLL.pa_context_kill_sink_input
pa_context_kill_sink_input.restype = POINTER(PA_OPERATION)
pa_context_kill_sink_input.argtypes = [POINTER(PA_CONTEXT), c_uint32, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_kill_client = DLL.pa_context_kill_client
pa_context_kill_client.restype = POINTER(PA_OPERATION)
pa_context_kill_client.argtypes = [POINTER(PA_CONTEXT), c_uint32, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_get_source_output_info_list = DLL.pa_context_get_source_output_info_list
pa_context_get_source_output_info_list.restype = POINTER(PA_OPERATION)
pa_context_get_source_output_info_list.argtypes = [POINTER(PA_CONTEXT), PA_SOURCE_OUTPUT_INFO_CB_T, c_void_p]

pa_context_move_source_output_by_index = DLL.pa_context_move_source_output_by_index
pa_context_move_source_output_by_index.restype = POINTER(PA_OPERATION)
pa_context_move_source_output_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_uint32, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_source_output_volume = DLL.pa_context_set_source_output_volume
pa_context_set_source_output_volume.restype = POINTER(PA_OPERATION)
pa_context_set_source_output_volume.argtypes = [POINTER(PA_CONTEXT), c_uint32, POINTER(PA_CVOLUME), PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_source_output_mute = DLL.pa_context_set_source_output_mute
pa_context_set_source_output_mute.restype = POINTER(PA_OPERATION)
pa_context_set_source_output_mute.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_get_source_info_list = DLL.pa_context_get_source_info_list
pa_context_get_source_info_list.restype = POINTER(PA_OPERATION)
pa_context_get_source_info_list.argtypes = [POINTER(PA_CONTEXT), PA_SOURCE_INFO_CB_T, c_void_p]

pa_context_set_source_volume_by_index = DLL.pa_context_set_source_volume_by_index
pa_context_set_source_volume_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_source_volume_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, POINTER(PA_CVOLUME), PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_source_mute_by_index = DLL.pa_context_set_source_mute_by_index
pa_context_set_source_mute_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_source_mute_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_suspend_source_by_index = DLL.pa_context_suspend_source_by_index
pa_context_suspend_source_by_index.restype = POINTER(PA_OPERATION)
pa_context_suspend_source_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_int, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_source_port_by_index = DLL.pa_context_set_source_port_by_index
pa_context_set_source_port_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_source_port_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_char_p, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_set_default_source = DLL.pa_context_set_default_source
pa_context_set_default_source.restype = POINTER(PA_OPERATION)
pa_context_set_default_source.argtypes = [POINTER(PA_CONTEXT), c_char_p, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_kill_source_output = DLL.pa_context_kill_source_output
pa_context_kill_source_output.restype = POINTER(PA_OPERATION)
pa_context_kill_source_output.argtypes = [POINTER(PA_CONTEXT), c_uint32, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_get_client_info_list = DLL.pa_context_get_client_info_list
pa_context_get_client_info_list.restype = POINTER(PA_OPERATION)
pa_context_get_client_info_list.argtypes = [POINTER(PA_CONTEXT), PA_CLIENT_INFO_CB_T, c_void_p]

pa_context_get_card_info_list = DLL.pa_context_get_card_info_list
pa_context_get_card_info_list.restype = POINTER(PA_OPERATION)
pa_context_get_card_info_list.argtypes = [POINTER(PA_CONTEXT), PA_CARD_INFO_CB_T, c_void_p]

pa_context_set_card_profile_by_index = DLL.pa_context_set_card_profile_by_index
pa_context_set_card_profile_by_index.restype = POINTER(PA_OPERATION)
pa_context_set_card_profile_by_index.argtypes = [POINTER(PA_CONTEXT), c_uint32, c_char_p, PA_CONTEXT_SUCCESS_CB_T, c_void_p]

pa_context_get_server_info = DLL.pa_context_get_server_info
pa_context_get_server_info.restype = POINTER(PA_OPERATION)
pa_context_get_server_info.argtypes = [POINTER(PA_CONTEXT), PA_SERVER_INFO_CB_T, c_void_p]

pa_get_library_version = DLL.pa_get_library_version
pa_get_library_version.restype = c_char_p
PA_MAJOR = int(pa_get_library_version().decode().split('.')[0])

# ^ bindings
#########################################################################################
# v lib


class DebugMixin():

    def debug(self):
        pprint(vars(self))


class PulsePort(DebugMixin):

    def __init__(self, pa_port):
        self.name = pa_port.name
        self.description = pa_port.description
        self.priority = pa_port.priority
        self.available = getattr(pa_port, "available", 0)
        if self.available == 1:  # 1 off, 0 n/a, 2 on
            self.description += b' / off'


class PulseServer(DebugMixin):

    def __init__(self, pa_server):
        self.default_sink_name = pa_server.default_sink_name
        self.default_source_name = pa_server.default_source_name
        self.server_version = pa_server.server_version


class PulseCardProfile(DebugMixin):

    def __init__(self, pa_profile):
        self.name = pa_profile.name
        self.description = pa_profile.description
        self.available = getattr(pa_profile, "available", 1)
        if not self.available:
            self.description += b' / off'


class PulseCard(DebugMixin):

    def __init__(self, pa_card):
        self.name = pa_card.name
        self.description = pa_proplist_gets(pa_card.proplist, b'device.description')
        self.index = pa_card.index
        self.driver = pa_card.driver
        self.owner_module = pa_card.owner_module
        self.n_profiles = pa_card.n_profiles
        if PA_MAJOR >= 5:
            self.profiles = [PulseCardProfile(pa_card.profiles2[n].contents) for n in range(self.n_profiles)]
            self.active_profile = PulseCardProfile(pa_card.active_profile2[0])
        else:  # fallback to legacy profile, for PA < 5.0 (March 2014)
            self.profiles = [PulseCardProfile(pa_card.profiles[n]) for n in range(self.n_profiles)]
            self.active_profile = PulseCardProfile(pa_card.active_profile[0])
        self.volume = type('volume', (object, ), {'channels': 1, 'values': [0, 0]})

    def __str__(self):
        return "Card-ID: {}, Name: {}".format(self.index, self.name.decode())


class PulseClient(DebugMixin):

    def __init__(self, pa_client):
        self.index = getattr(pa_client, "index", 0)
        self.name = getattr(pa_client, "name", pa_client)
        self.driver = getattr(pa_client, "driver", "default driver")
        self.owner_module = getattr(pa_client, "owner_module", -1)

    def __str__(self):
        return "Client-name: {}".format(self.name.decode())


class Pulse(DebugMixin):

    def __init__(self, client_name='libpulse', server_name=None, reconnect=False):
        self.error = None
        self.data = []
        self.operation = None
        self.connected = False
        self.client_name = client_name.encode()
        self.server_name = server_name

        self.pa_state_cb = PA_STATE_CB_T(self.state_cb)
        self.pa_subscribe_cb = self.pa_dc_cb = lambda: None
        self.pa_cbs = {'sink_input_list':    PA_SINK_INPUT_INFO_CB_T(self.sink_input_list_cb),
                       'source_output_list': PA_SOURCE_OUTPUT_INFO_CB_T(self.source_output_list_cb),
                       'sink_list':          PA_SINK_INFO_CB_T(self.sink_list_cb),
                       'source_list':        PA_SOURCE_INFO_CB_T(self.source_list_cb),
                       'server':             PA_SERVER_INFO_CB_T(self.server_cb),
                       'card_list':          PA_CARD_INFO_CB_T(self.card_list_cb),
                       'client_list':        PA_CLIENT_INFO_CB_T(self.client_list_cb),
                       'success':            PA_CONTEXT_SUCCESS_CB_T(self.context_success)}
        self.mainloop = pa_threaded_mainloop_new()
        self.mainloop_api = pa_threaded_mainloop_get_api(self.mainloop)

        proplist = pa_proplist_new()
        pa_proplist_sets(proplist, b'application.id', self.client_name)
        pa_proplist_sets(proplist, b'application.icon_name', b'audio-card')
        self.context = pa_context_new_with_proplist(self.mainloop_api, self.client_name, proplist)
        pa_context_set_state_callback(self.context, self.pa_state_cb, None)
        pa_proplist_free(proplist)

        if pa_context_connect(self.context, self.server_name, 0, None) < 0 or self.error:
            if not reconnect: sys.exit("Failed to connect to pulseaudio: Connection refused")
            else: return

        pa_threaded_mainloop_lock(self.mainloop)
        pa_threaded_mainloop_start(self.mainloop)
        if self.error and reconnect: return
        pa_threaded_mainloop_wait(self.mainloop) or pa_threaded_mainloop_unlock(self.mainloop)
        if self.error and reconnect: return
        elif self.error: sys.exit('Failed to connect to pulseaudio')
        self.connected = True

    def wait_and_unlock(self):
        pa_threaded_mainloop_wait(self.mainloop)
        pa_threaded_mainloop_unlock(self.mainloop)
        pa_operation_unref(self.operation)

    def reconnect(self):
        if self.context:
            pa_context_disconnect(self.context)
            pa_context_unref(self.context)
        if self.mainloop:
            pa_threaded_mainloop_stop(self.mainloop)
            pa_threaded_mainloop_free(self.mainloop)
        self.__init__(self.client_name.decode(), self.server_name, reconnect=True)

    def unmute_stream(self, obj):
        if type(obj) is PulseSinkInfo:
            self.sink_mute(obj.index, 0)
        elif type(obj) is PulseSinkInputInfo:
            self.sink_input_mute(obj.index, 0)
        elif type(obj) is PulseSourceInfo:
            self.source_mute(obj.index, 0)
        elif type(obj) is PulseSourceOutputInfo:
            self.source_output_mute(obj.index, 0)
        obj.mute = 0

    def mute_stream(self, obj):
        if type(obj) is PulseSinkInfo:
            self.sink_mute(obj.index, 1)
        elif type(obj) is PulseSinkInputInfo:
            self.sink_input_mute(obj.index, 1)
        elif type(obj) is PulseSourceInfo:
            self.source_mute(obj.index, 1)
        elif type(obj) is PulseSourceOutputInfo:
            self.source_output_mute(obj.index, 1)
        obj.mute = 1

    def set_volume(self, obj, volume):
        if type(obj) is PulseSinkInfo:
            self.set_sink_volume(obj.index, volume)
        elif type(obj) is PulseSinkInputInfo:
            self.set_sink_input_volume(obj.index, volume)
        elif type(obj) is PulseSourceInfo:
            self.set_source_volume(obj.index, volume)
        elif type(obj) is PulseSourceOutputInfo:
            self.set_source_output_volume(obj.index, volume)
        obj.volume = volume

    def change_volume_mono(self, obj, inc):
        obj.volume.values = [v + inc for v in obj.volume.values]
        self.set_volume(obj, obj.volume)

    def get_volume_mono(self, obj):
        return int(sum(obj.volume.values) / len(obj.volume.values))

    def fill_clients(self):
        if not self.data:
            return None
        data, self.data = self.data, []
        clist = self.client_list()
        for d in data:
            for c in clist:
                if c.index == d.client_id:
                    d.client = c
                    break
        return data

    def state_cb(self, c, b):
        state = pa_context_get_state(c)
        if state == PA_CONTEXT_READY:
            pa_threaded_mainloop_signal(self.mainloop, 0)
        elif state == PA_CONTEXT_FAILED:
            self.error = RuntimeError("Failed to complete action: {}, {}".format(state, pa_context_errno(c)))
            self.connected = False
            pa_threaded_mainloop_signal(self.mainloop, 0)
            self.pa_dc_cb()
        return 0

    def _eof_cb(func):
        def wrapper(self, c, info, eof, *args):
            if eof:
                pa_threaded_mainloop_signal(self.mainloop, 0)
                return 0
            func(self, c, info, eof, *args)
            return 0
        return wrapper

    def _action_sync(func):
        def wrapper(self, *args):
            if self.error: raise self.error
            pa_threaded_mainloop_lock(self.mainloop)
            try:
                func(self, *args)
            except Exception as e:
                pa_threaded_mainloop_unlock(self.mainloop)
                raise e
            self.wait_and_unlock()
            if func.__name__ in ('sink_input_list', 'source_output_list'):
                self.data = self.fill_clients()
            data, self.data = self.data, []
            return data or []
        return wrapper

    @_eof_cb
    def card_list_cb(self, c, card_info, eof, userdata):
        self.data.append(PulseCard(card_info[0]))

    @_eof_cb
    def client_list_cb(self, c, client_info, eof, userdata):
        self.data.append(PulseClient(client_info[0]))

    @_eof_cb
    def sink_input_list_cb(self, c, sink_input_info, eof, userdata):
        self.data.append(PulseSinkInputInfo(sink_input_info[0]))

    @_eof_cb
    def sink_list_cb(self, c, sink_info, eof, userdata):
        self.data.append(PulseSinkInfo(sink_info[0]))

    @_eof_cb
    def source_output_list_cb(self, c, source_output_info, eof, userdata):
        self.data.append(PulseSourceOutputInfo(source_output_info[0]))

    @_eof_cb
    def source_list_cb(self, c, source_info, eof, userdata):
        self.data.append(PulseSourceInfo(source_info[0]))

    def server_cb(self, c, server_info, userdata):
        self.data = PulseServer(server_info[0])
        pa_threaded_mainloop_signal(self.mainloop, 0)

    def context_success(self, *_):
        pa_threaded_mainloop_signal(self.mainloop, 0)

    def subscribe(self, cb):
        self.pa_subscribe_cb, self.pa_dc_cb = PA_CONTEXT_SUBSCRIBE_CB_T(cb), cb
        pa_context_set_subscribe_callback(self.context, self.pa_subscribe_cb, None)
        pa_threaded_mainloop_lock(self.mainloop)
        self.operation = pa_context_subscribe(self.context, PA_SUBSCRIPTION_MASK_ALL, self.pa_cbs['success'], None)
        self.wait_and_unlock()

    @_action_sync
    def sink_input_list(self):
        self.operation = pa_context_get_sink_input_info_list(self.context, self.pa_cbs['sink_input_list'], None)

    @_action_sync
    def source_output_list(self):
        self.operation = pa_context_get_source_output_info_list(self.context, self.pa_cbs['source_output_list'], None)

    @_action_sync
    def sink_list(self):
        self.operation = pa_context_get_sink_info_list(self.context, self.pa_cbs['sink_list'], None)

    @_action_sync
    def source_list(self):
        self.operation = pa_context_get_source_info_list(self.context, self.pa_cbs['source_list'], None)

    @_action_sync
    def get_server_info(self):
        self.operation = pa_context_get_server_info(self.context, self.pa_cbs['server'], None)

    @_action_sync
    def card_list(self):
        self.operation = pa_context_get_card_info_list(self.context, self.pa_cbs['card_list'], None)

    @_action_sync
    def client_list(self):
        self.operation = pa_context_get_client_info_list(self.context, self.pa_cbs['client_list'], None)

    @_action_sync
    def sink_input_mute(self, index, mute):
        self.operation = pa_context_set_sink_input_mute(self.context, index, mute, self.pa_cbs['success'], None)

    @_action_sync
    def sink_input_move(self, index, s_index):
        self.operation = pa_context_move_sink_input_by_index(self.context, index, s_index, self.pa_cbs['success'], None)

    @_action_sync
    def sink_mute(self, index, mute):
        self.operation = pa_context_set_sink_mute_by_index(self.context, index, mute, self.pa_cbs['success'], None)

    @_action_sync
    def set_sink_input_volume(self, index, vol):
        self.operation = pa_context_set_sink_input_volume(self.context, index, vol.to_c(), self.pa_cbs['success'], None)

    @_action_sync
    def set_sink_volume(self, index, vol):
        self.operation = pa_context_set_sink_volume_by_index(self.context, index, vol.to_c(), self.pa_cbs['success'], None)

    @_action_sync
    def sink_suspend(self, index, suspend):
        self.operation = pa_context_suspend_sink_by_index(self.context, index, suspend, self.pa_cbs['success'], None)

    @_action_sync
    def set_default_sink(self, name):
        self.operation = pa_context_set_default_sink(self.context, name, self.pa_cbs['success'], None)

    @_action_sync
    def kill_sink(self, index):
        self.operation = pa_context_kill_sink_input(self.context, index, self.pa_cbs['success'], None)

    @_action_sync
    def kill_client(self, index):
        self.operation = pa_context_kill_client(self.context, index, self.pa_cbs['success'], None)

    @_action_sync
    def set_sink_port(self, index, port):
        self.operation = pa_context_set_sink_port_by_index(self.context, index, port, self.pa_cbs['success'], None)

    @_action_sync
    def set_source_output_volume(self, index, vol):
        self.operation = pa_context_set_source_output_volume(self.context, index, vol.to_c(), self.pa_cbs['success'], None)

    @_action_sync
    def set_source_volume(self, index, vol):
        self.operation = pa_context_set_source_volume_by_index(self.context, index, vol.to_c(), self.pa_cbs['success'], None)

    @_action_sync
    def source_suspend(self, index, suspend):
        self.operation = pa_context_suspend_source_by_index(self.context, index, suspend, self.pa_cbs['success'], None)

    @_action_sync
    def set_default_source(self, name):
        self.operation = pa_context_set_default_source(self.context, name, self.pa_cbs['success'], None)

    @_action_sync
    def kill_source(self, index):
        self.operation = pa_context_kill_source_output(self.context, index, self.pa_cbs['success'], None)

    @_action_sync
    def set_source_port(self, index, port):
        self.operation = pa_context_set_source_port_by_index(self.context, index, port, self.pa_cbs['success'], None)

    @_action_sync
    def source_output_mute(self, index, mute):
        self.operation = pa_context_set_source_output_mute(self.context, index, mute, self.pa_cbs['success'], None)

    @_action_sync
    def source_mute(self, index, mute):
        self.operation = pa_context_set_source_mute_by_index(self.context, index, mute, self.pa_cbs['success'], None)

    @_action_sync
    def source_output_move(self, index, s_index):
        self.operation = pa_context_move_source_output_by_index(self.context, index, s_index, self.pa_cbs['success'], None)

    @_action_sync
    def set_card_profile(self, index, p_index):
        self.operation = pa_context_set_card_profile_by_index(self.context, index, p_index, self.pa_cbs['success'], None)


class PulseSink(DebugMixin):

    def __init__(self, sink_info):
        self.index = sink_info.index
        self.name = sink_info.name
        self.mute = sink_info.mute
        self.volume = PulseVolume(sink_info.volume)


class PulseSinkInfo(PulseSink):

    def __init__(self, pa_sink_info):
        PulseSink.__init__(self, pa_sink_info)
        self.description = pa_sink_info.description
        self.owner_module = pa_sink_info.owner_module
        self.driver = pa_sink_info.driver
        self.monitor_source = pa_sink_info.monitor_source
        self.monitor_source_name = pa_sink_info.monitor_source_name
        self.n_ports = pa_sink_info.n_ports
        self.ports = [PulsePort(pa_sink_info.ports[i].contents) for i in range(self.n_ports)]
        self.active_port = None
        if self.n_ports:
            self.active_port = PulsePort(pa_sink_info.active_port.contents)

    def __str__(self):
        return "ID: sink-{}, Name: {}, Mute: {}, {}".format(self.index, self.description.decode(), self.mute, self.volume)


class PulseSinkInputInfo(PulseSink):

    def __init__(self, pa_sink_input_info):
        PulseSink.__init__(self, pa_sink_input_info)
        self.owner_module = pa_sink_input_info.owner_module
        self.client = PulseClient(pa_sink_input_info.name)
        self.client_id = pa_sink_input_info.client
        self.sink = self.owner = pa_sink_input_info.sink
        self.driver = pa_sink_input_info.driver
        self.media_name = pa_proplist_gets(pa_sink_input_info.proplist, b'media.name')

    def __str__(self):
        if self.client:
            return "ID: sink-input-{}, Name: {}, Mute: {}, {}".format(self.index, self.client.name.decode(), self.mute, self.volume)
        return "ID: sink-input-{}, Name: {}, Mute: {}".format(self.index, self.name.decode(), self.mute)


class PulseSource(DebugMixin):

    def __init__(self, source_info):
        self.index = source_info.index
        self.name = source_info.name
        self.mute = source_info.mute
        self.volume = PulseVolume(source_info.volume)


class PulseSourceInfo(PulseSource):

    def __init__(self, pa_source_info):
        PulseSource.__init__(self, pa_source_info)
        self.description = pa_source_info.description
        self.owner_module = pa_source_info.owner_module
        self.monitor_of_sink = pa_source_info.monitor_of_sink
        self.monitor_of_sink_name = pa_source_info.monitor_of_sink_name
        self.driver = pa_source_info.driver
        self.n_ports = pa_source_info.n_ports
        self.ports = [PulsePort(pa_source_info.ports[i].contents) for i in range(self.n_ports)]
        self.active_port = None
        if self.n_ports:
            self.active_port = PulsePort(pa_source_info.active_port.contents)

    def __str__(self):
        return "ID: source-{}, Name: {}, Mute: {}, {}".format(self.index, self.description.decode(), self.mute, self.volume)


class PulseSourceOutputInfo(PulseSource):

    def __init__(self, pa_source_output_info):
        PulseSource.__init__(self, pa_source_output_info)
        self.owner_module = pa_source_output_info.owner_module
        self.client = PulseClient(pa_source_output_info.name)
        self.client_id = pa_source_output_info.client
        self.source = self.owner = pa_source_output_info.source
        self.driver = pa_source_output_info.driver
        self.application_id = pa_proplist_gets(pa_source_output_info.proplist, b'application.id')

    def __str__(self):
        if self.client:
            return "ID: source-output-{}, Name: {}, Mute: {}, {}".format(self.index, self.client.name.decode(), self.mute, self.volume)
        return "ID: source-output-{}, Name: {}, Mute: {}".format(self.index, self.name.decode(), self.mute)


class PulseVolume(DebugMixin):

    def __init__(self, cvolume):
        self.channels = cvolume.channels
        self.values = [(round(x * 100 / PA_VOLUME_NORM)) for x in cvolume.values[:self.channels]]
        self.cvolume = PA_CVOLUME()
        self.cvolume.channels = self.channels

    def to_c(self):
        self.values = list(map(lambda x: max(min(x, 150), 0), self.values))
        for x in range(self.channels):
            self.cvolume.values[x] = round((self.values[x] * PA_VOLUME_NORM) / 100)
        return self.cvolume

    def __str__(self):
        return "Channels: {}, Volumes: {}".format(self.channels, [str(x) + "%" for x in self.values])


# ^ lib
#########################################################################################
# v main


class Bar():
    # should be in correct order
    LEFT, RIGHT, RLEFT, RRIGHT, CENTER, SUB, SLEFT, SRIGHT, NONE = range(9)

    def __init__(self, pa):
        if type(pa) is str:
            self.name = pa
            return
        if type(pa) in (PulseSinkInfo, PulseSourceInfo, PulseCard):
            self.fullname = pa.description.decode()
        else:
            self.fullname = pa.client.name.decode()
        self.name = re.sub(r'^ALSA plug-in \[|\]$', '', self.fullname.replace('|', ' '))
        for key in CFG.renames:
            if key.match(self.name):
                self.name = CFG.renames[key]
                break
        self.index = pa.index
        self.owner = -1
        self.stream_index = -1
        self.media_name, self.media_name_wide, self.media_name_widths = '', False, []
        self.poll_data(pa, 0, 0)
        self.maxsize = 150
        self.locked = True

    def poll_data(self, pa, owned, stream_index):
        self.channels = pa.volume.channels
        self.muted = getattr(pa, 'mute', False)
        self.owned = owned
        self.stream_index = stream_index
        self.volume = pa.volume.values
        if hasattr(pa, 'media_name'):
            media_fullname = pa.media_name.decode().replace('\n', ' ')
            media_name = ': {}'.format(media_fullname.replace('|', ' '))
            if media_fullname != self.fullname and media_name != self.media_name:
                self.media_name, self.media_name_wide = media_name, False
                if len(media_fullname) != len(pa.media_name):  # contains multi-byte chars which might be wide
                    self.media_name_widths = [int(east_asian_width(c) == 'W') + 1 for c in media_name]
                    self.media_name_wide = 2 in self.media_name_widths
        else:
            self.media_name, self.media_name_wide = '', False
        if type(pa) in (PulseSinkInputInfo, PulseSourceOutputInfo):
            self.owner = pa.owner
        self.pa = pa

    def mute_toggle(self):
        PULSE.unmute_stream(self.pa) if self.muted else PULSE.mute_stream(self.pa)

    def lock_toggle(self):
        self.locked = not self.locked

    def set(self, n, side):
        vol = self.pa.volume
        if self.locked:
            for i, _ in enumerate(vol.values):
                vol.values[i] = n
        else:
            vol.values[side] = n
        PULSE.set_volume(self.pa, vol)

    def move(self, n, side):
        vol = self.pa.volume
        if self.locked:
            for i, _ in enumerate(vol.values):
                vol.values[i] += n
        else:
            vol.values[side] += n
        PULSE.set_volume(self.pa, vol)


class Screen():
    DOWN = 1
    UP = -1
    SCROLL_UP = [getattr(curses, i, 0) for i in ['BUTTON4_PRESSED', 'BUTTON3_TRIPLE_CLICKED']]
    SCROLL_DOWN = [getattr(curses, i, 0) for i in ['BUTTON5_PRESSED', 'A_LOW', 'A_BOLD', 'BUTTON4_DOUBLE_CLICKED']]
    KEY_MOUSE = getattr(curses, 'KEY_MOUSE', 0)
    DIGITS = list(map(ord, map(str, range(10))))
    SIDES = {Bar.LEFT: 'Left', Bar.RIGHT: 'Right', Bar.RLEFT: 'Rear Left',
             Bar.RRIGHT: 'Rear Right', Bar.CENTER: 'Center', Bar.SUB: 'Subwoofer',
             Bar.SLEFT: 'Side left', Bar.SRIGHT: 'Side right'}
    SEQ_TO_KEY = {159: curses.KEY_F1, 160: curses.KEY_F2, 161: curses.KEY_F3,
                  316: curses.KEY_SRIGHT, 317: curses.KEY_SLEFT,
                  151: curses.KEY_HOME, 266: curses.KEY_HOME,
                  149: curses.KEY_END, 269: curses.KEY_END}

    def __init__(self, color=2, mouse=True):
        os.environ['ESCDELAY'] = '25'
        self.screen = curses.initscr()
        self.screen.nodelay(True)
        self.screen.scrollok(1)
        if mouse:
            try:
                curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.BUTTON1_CLICKED | self.KEY_MOUSE |
                                 functools.reduce(operator.or_, list(self.SCROLL_UP)) |
                                 functools.reduce(operator.or_, list(self.SCROLL_DOWN)))
            except:
                self.KEY_MOUSE = 0
        else:
            self.KEY_MOUSE = 0
        try:
            curses.curs_set(0)
        except:  # terminal doesn't support visibility requests
            pass
        self.screen.border(0)
        self.screen.clear()
        self.screen.refresh()
        self.index = 0
        self.top_line_num = 0
        self.focus_line_num = 0
        self.lines, self.cols = curses.LINES - 2, curses.COLS - 1
        self.info, self.menu = str, str
        self.mode_keys = self.get_mode_keys()
        self.menu_titles = ['{} Output'.format(self.mode_keys[0]),
                            '{} Input'.format(self.mode_keys[1]),
                            '{} Cards'.format(self.mode_keys[2])]
        self.data = []
        self.mode = {0: 1, 1: 0, 2: 0}
        self.modes_data = [[[], 0, 0] for i in range(6)]
        self.active_mode = 0
        self.old_mode = 0
        self.change_mode_allowed = True
        self.n_lines = 0
        self.color_mode = color
        if color in (1, 2) and curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_YELLOW, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)
            self.green = curses.color_pair(1)
            self.yellow = curses.color_pair(2)
            self.red = curses.color_pair(3)
            n = 7 if curses.COLORS < 256 else 67
            curses.init_pair(n, n - 1, -1)
            self.muted_color = curses.color_pair(n)
            if curses.COLORS < 256:
                self.gray_gradient = [curses.A_NORMAL] * 3
            else:
                try:
                    curses.init_pair(240, 240, -1)
                    curses.init_pair(243, 243, -1)
                    curses.init_pair(246, 246, -1)
                    self.gray_gradient = [curses.color_pair(240),
                                          curses.color_pair(243),
                                          curses.color_pair(246)]
                except:
                    self.gray_gradient = [curses.A_NORMAL] * 3
        else:
            # if term has colors start them regardless of --color to avoid weird backgrounds on some terminals
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
            self.gray_gradient = [curses.A_NORMAL] * 3
            self.green = self.yellow = self.red = self.muted_color = curses.A_NORMAL
        self.gradient = [self.green, self.yellow, self.red]
        self.submenu_data = []
        self.submenu_width = 30
        self.submenu_show = False
        self.submenu = curses.newwin(curses.LINES, 0, 0, 0)
        self.helpwin_show = False
        self.helpwin = curses.newwin(14, 50, 0, 0)
        try:
            self.helpwin.mvwin((curses.LINES // 2) - 7, (curses.COLS // 2) - 25)
        except:
            pass
        self.selected = None
        self.action = None
        self.server_info = None
        self.ev = threading.Event()

    def getch(self):
        # blocking getch, can be 'interrupted' by ev.set
        self.ev.wait()
        self.ev.clear()
        c = self.screen.getch()
        if c == 27:  # collect escape sequences as a single key
            seq_sum = sum(takewhile(lambda x: x != -1, [self.screen.getch() for _ in range(5)]))
            c = self.SEQ_TO_KEY.get(seq_sum, seq_sum + 128 if seq_sum else 27)
        return c

    def pregetcher(self):
        # because curses.getch doesn't work well with threads
        while True:
            select([sys.stdin], [], [], 10)
            self.ev.set()

    def wake_cb(self, *_):
        self.ev.set()

    def display_line(self, index, line, mod=curses.A_NORMAL, win=None):
        shift, win = 0, win or self.screen
        for i in line.split('\n'):
            parts = i.rsplit('|')
            head = ''.join(parts[:-1])
            tail = int(parts[-1] or 0)
            try:
                win.addstr(index, shift, head, tail | mod)
            except:
                win.addstr(min(curses.LINES - 1, index), min(curses.COLS - 1, shift), head, tail | mod)
            shift += len(head)

    def change_mode(self, mode):
        if not self.change_mode_allowed:
            return
        self.modes_data[self.active_mode][1] = self.focus_line_num
        self.modes_data[self.active_mode][2] = self.top_line_num
        self.old_mode = self.active_mode
        self.mode = self.mode.fromkeys(self.mode, 0)
        self.mode[mode] = 1
        self.focus_line_num = self.modes_data[mode][1]
        self.top_line_num = self.modes_data[mode][2]
        self.active_mode = mode
        self.get_data()

    def cycle_mode(self, direction=1):
        for mode, active in self.mode.items():
            if active == 1:
                self.change_mode((mode + direction) % 3)
                return

    def update_menu(self):
        if self.change_mode_allowed:
            self.menu = '{}|{}\n  {}|{}\n  {}|{}\n {:>{}}|{}'.format(
                self.menu_titles[0], curses.A_BOLD if self.mode[0] else curses.A_DIM,
                self.menu_titles[1], curses.A_BOLD if self.mode[1] else curses.A_DIM,
                self.menu_titles[2], curses.A_BOLD if self.mode[2] else curses.A_DIM,
                "? - help", self.cols - 30, curses.A_DIM)
        else:
            selected = 'output' if type(self.selected[0].pa) is PulseSinkInputInfo else 'input'
            self.menu = "Select new {} device:|{}".format(selected, curses.A_NORMAL)

    def update_info(self):
        focus, bottom = self.focus_line_num + self.top_line_num + 1, self.top_line_num + self.lines
        try:
            bar, side = self.data[focus - 1][0], self.data[focus - 1][1]
        except IndexError:
            self.focus_line_num, self.top_line_num = 0, 0
            for _ in range(len(self.data)): self.scroll(self.UP)
            return
        if side is Bar.NONE:
            self.info = str
            return
        side = 'All' if bar.locked else 'Mono' if bar.channels == 1 else self.SIDES[side]
        more = '↕' if bottom < self.n_lines and self.top_line_num > 0 else '↑' if self.top_line_num > 0 else '↓' if bottom < self.n_lines else ' '
        name = '{}: {}'.format(bar.name, side)
        if len(name) > self.cols - 8:
            name = '{}: {}'.format(bar.name[:self.cols - (10 + len(side))].strip(), side)
        locked = '{}|{}'.format(CFG.style.info_locked, self.red) if bar.locked else '{}|{}'.format(CFG.style.info_unlocked, curses.A_DIM)
        muted  = '{}|{}'.format(CFG.style.info_muted, self.red) if bar.muted else '{}|{}'.format(CFG.style.info_unmuted, curses.A_DIM)
        self.info = '{}\n {}\n  {}|{}\n{:>{}}|0'.format(locked, muted, name, curses.A_NORMAL, more, self.cols - len(name) - 5)

    def run_mouse(self):
        try:
            _, x, y, _, c = curses.getmouse()
            if c & curses.BUTTON1_CLICKED:
                if y > 0:
                    top, bottom = self.top_line_num, len(self.data[self.top_line_num:self.top_line_num + self.lines]) - 1
                    if y - 1 <= bottom:
                        self.focus_line_num = max(top, min(bottom, y - 1))
                else:
                    f1 = len(self.menu_titles[0]) + 1  # 1 is 'spacing' after the title
                    f2 = f1 + len(self.menu_titles[1]) + 2
                    f3 = f2 + len(self.menu_titles[2]) + 3
                    if x in range(0, f1):
                        self.change_mode(0)
                    elif x in range(f1, f2):
                        self.change_mode(1)
                    elif x in range(f2, f3):
                        self.change_mode(2)
            return c
        except curses.error:
            return None

    def resize(self):
        curses.COLS, curses.LINES = get_terminal_size()
        curses.resizeterm(curses.LINES, curses.COLS)
        self.submenu.resize(curses.LINES, self.submenu_width + 1)
        if self.submenu_show:
            self.submenu_show = False
            self.focus_line_num = self.modes_data[5][1]
            self.top_line_num = self.modes_data[5][2]
        try:
            self.helpwin.resize(14, 50)
            self.helpwin.mvwin((curses.LINES // 2) - 7, (curses.COLS // 2) - 25)
        except curses.error:
            pass
        self.helpwin_show = False
        self.lines, self.cols = curses.LINES - 2, curses.COLS - 1
        self.ev.set()

    def terminate(self):
        # if ^C pressed while sleeping in reconnect wrapper.restore won't be called
        # so have to restore it manually here
        self.screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        sys.exit()

    def reconnect(self):
        self.focus_line_num = 0
        self.menu = self.info = str
        self.data = [(Bar('PA - Connection refused.\nTrying to reconnect.'), Bar.NONE, 0)]
        while not PULSE.connected:
            self.display()
            if self.screen.getch() in CFG.keys.quit: sys.exit()
            PULSE.reconnect()
            sleep(0.5)
        PULSE.subscribe(self.wake_cb)
        self.ev.set()

    def run(self, _):
        signal.signal(signal.SIGINT, lambda s, f: self.terminate())
        signal.signal(signal.SIGTERM, lambda s, f: self.terminate())
        signal.signal(signal.SIGWINCH, lambda s, f: self.resize())
        threading.Thread(target=self.pregetcher, daemon=True).start()
        PULSE.subscribe(self.wake_cb)
        self.ev.set()
        while True:
            try:
                if not self.submenu_show:
                    try:
                        self.get_data()
                    except RuntimeError:
                        self.reconnect()
                    except IndexError:
                        self.scroll(self.UP)
                    if self.helpwin_show:
                        self.display_helpwin()
                        self.run_helpwin()
                        continue
                    self.update_menu()
                    self.update_info()
                    self.display()
                elif self.change_mode_allowed:
                    self.display_submenu()
                    self.run_submenu()
                    continue
            except (curses.error, IndexError, ValueError) as e:
                self.screen.erase()
                self.screen.addstr("Terminal *might* be too small {}:{}\n".format(curses.LINES, curses.COLS))
                self.screen.addstr("{}\n{}\n".format(str(self.mode), str(e)))
                self.screen.addstr(str(traceback.extract_tb(e.__traceback__)))

            c = self.getch()
            if c == -1: continue

            focus = self.top_line_num + self.focus_line_num
            bar, side = self.data[focus][0], self.data[focus][1]

            if c == self.KEY_MOUSE:
                c = self.run_mouse() or c

            if c in CFG.keys.mode1:
                self.change_mode(0)
            elif c in CFG.keys.mode2:
                self.change_mode(1)
            elif c in CFG.keys.mode3:
                self.change_mode(2)
            elif c == ord('?'):
                self.helpwin_show = True
            elif c == ord('\n'):
                if not self.submenu_show and self.change_mode_allowed and side != Bar.NONE:
                    self.selected = self.data[focus]
                    if type(self.selected[0].pa) in (PulseSinkInfo, PulseSourceInfo):
                        self.submenu_data = ['Suspend', 'Resume', 'Set as default']
                        if self.selected[0].pa.n_ports:
                            self.submenu_data.append('Set port')
                    elif type(self.selected[0].pa) is PulseCard:
                        self.fill_submenu_pa(target='profile', off=0, hide=CFG.ui.hide_unavailable_profiles)
                    else:
                        self.submenu_data = ['Move', 'Kill']
                    self.submenu_show = True
                    self.modes_data[5][0] = 0
                    self.modes_data[5][1] = self.focus_line_num
                    self.modes_data[5][2] = self.top_line_num
                    self.focus_line_num = self.top_line_num = 0
                    self.n_lines = len(self.submenu_data)
                    self.resize_submenu()
                elif not self.change_mode_allowed:
                    self.submenu_show = False
                    self.change_mode_allowed = True
                    if self.action == 'Move':
                        if type(self.selected[0].pa) is PulseSinkInputInfo:
                            PULSE.sink_input_move(self.selected[0].index, self.data[focus][0].pa.index)
                        elif type(self.selected[0].pa) is PulseSourceOutputInfo:
                            PULSE.source_output_move(self.selected[0].index, self.data[focus][0].pa.index)
                        self.change_mode(self.old_mode)
                        self.focus_line_num = self.modes_data[5][1]
                        self.top_line_num = self.modes_data[5][2]
                    else:
                        self.change_mode(self.old_mode)
            elif c in CFG.keys.next_mode:
                self.cycle_mode()
            elif c in CFG.keys.prev_mode:
                self.cycle_mode(direction=-1)
            elif c in CFG.keys.quit:
                if not self.change_mode_allowed:
                    self.submenu_show = False
                    self.change_mode_allowed = True
                    self.change_mode(self.old_mode)
                    self.focus_line_num = self.modes_data[5][1]
                    self.top_line_num = self.modes_data[5][2]
                else:
                    sys.exit()

            if side is Bar.NONE:
                continue

            if c in CFG.keys.up:
                if bar.locked:
                    if self.data[focus][1] == 0:
                        n = 1
                    else:
                        n = self.data[focus][1] + 1
                    for _ in range(n): self.scroll(self.UP)
                else:
                    self.scroll(self.UP)
                if not self.data[self.top_line_num + self.focus_line_num][0]:
                    self.scroll(self.UP)
            elif c in CFG.keys.down:
                if bar.locked:
                    if self.data[focus][1] == self.data[focus][3] - 1:
                        n = 1
                    else:
                        n = ((self.data[focus][3] - 1) - self.data[focus][1]) + 1
                    for _ in range(n): self.scroll(self.DOWN)
                else:
                    self.scroll(self.DOWN)
                if not self.data[self.top_line_num + self.focus_line_num][0]:
                    self.scroll(self.DOWN)
            elif c in CFG.keys.top:
                self.scroll_first()
            elif c in CFG.keys.bottom:
                self.scroll_last()

            elif c in CFG.keys.mute:
                bar.mute_toggle()
            elif c in CFG.keys.lock:
                bar.lock_toggle()
            elif c in CFG.keys.left or any([c & i for i in self.SCROLL_DOWN]):
                bar.move(-CFG.general.step, side)
            elif c in CFG.keys.right or any([c & i for i in self.SCROLL_UP]):
                bar.move(CFG.general.step, side)
            elif c in CFG.keys.left_big:
                bar.move(-CFG.general.step_big, side)
            elif c in CFG.keys.right_big:
                bar.move(CFG.general.step_big, side)
            elif c in self.DIGITS:
                percent = int(chr(c)) * 10
                bar.set(100 if percent == 0 else percent, side)

    def fill_submenu_pa(self, target, off, hide):
        self.submenu_data = []
        active = getattr(self.selected[0].pa, "active_" + target).description.decode()
        for i in getattr(self.selected[0].pa, target + "s"):
            description = i.description.decode()
            if active == description:
                self.submenu_data.append(' {}|{}'.format(description, self.green))
            else:
                if hide and i.available == off: continue
                self.submenu_data.append(' {}|{}'.format(description, curses.A_DIM if i.available == off else 0))

    def build(self, target, devices, streams):
        tmp = []
        index = 0
        for device in devices:
            index += device.volume.channels
            stream_index = device.volume.channels
            tmp.append([device, device.volume.channels, index, stream_index])
            device_index = len(tmp) - 1
            for stream in streams:
                if stream.owner == device.index:
                    index += stream.volume.channels
                    stream_index += stream.volume.channels
                    tmp.append([stream, -1, index, stream_index])
                    tmp[device_index][1] += stream.volume.channels
            tmp[-1][1] = tmp[device_index][1]
        for s in tmp:
            found = False
            for i, data in enumerate(target):
                if s[0].index == data[2] and type(s[0]) == type(data[0].pa):
                    found = True
                    data[0].poll_data(s[0], s[1], s[3])
                    y = s[2] - (data[3] - data[1])
                    target[i], target[y] = target[y], target[i]
            if not found:
                bar = Bar(s[0])
                bar.owned = s[1]
                bar.stream_index = s[3]
                for c in range(s[0].volume.channels):
                    target.append((bar, c, s[0].index, s[0].volume.channels))
        for i in reversed(range(len(target))):
            data = target[i]
            for s in tmp:
                if s[0].index == data[2] and type(s[0]) == type(data[0].pa):
                    y = s[2] - (data[3] - data[1])
                    target[i], target[y] = target[y], target[i]
                    break
            else:
                del target[i]
                if self.focus_line_num + self.top_line_num >= i:
                    self.scroll(self.UP)
        return target

    def add_spacers(self, f):
        tmp = []
        l = len(f)
        for i, s in enumerate(f):
            tmp.append(s)
            if s[0].stream_index == s[0].owned and s[1] == s[0].channels - 1 and i != l - 1:
                tmp.append((None, -1, 0, 0))
        return tmp

    def get_data(self):
        if self.mode[0]:
            self.data = self.build(self.modes_data[0][0], PULSE.sink_list(), PULSE.sink_input_list())
            self.data = self.add_spacers(self.data)
        elif self.mode[1]:
            ids = (b'org.PulseAudio.pavucontrol', b'org.gnome.VolumeControl', b'org.kde.kmixd', b'pulsemixer')
            source_output_list = [s for s in PULSE.source_output_list() if s.application_id not in ids]
            self.data = self.build(self.modes_data[1][0], PULSE.source_list(), source_output_list)
            self.data = self.add_spacers(self.data)
        elif self.mode[2]:
            self.data = self.build(self.modes_data[2][0], PULSE.card_list(), [])
        elif type(self.selected[0].pa) is PulseSinkInputInfo:
            self.data = self.build(self.modes_data[3][0], PULSE.sink_list(), [])
        elif type(self.selected[0].pa) is PulseSourceOutputInfo:
            self.data = self.build(self.modes_data[4][0], PULSE.source_list(), [])
        self.server_info = PULSE.get_server_info()
        self.n_lines = len(self.data)
        if not self.n_lines:
            self.focus_line_num = 0
            self.data.append((Bar('no data'), Bar.NONE, 0))
        if not self.data[self.top_line_num + self.focus_line_num][0]:
            self.scroll(self.UP)

    def display(self):
        self.screen.erase()
        top = self.top_line_num
        bottom = self.top_line_num + self.lines
        self.display_line(0, self.menu)
        for index, line in enumerate(self.data[top:bottom]):
            bar, bartype = line[0], line[1]
            if not bar:
                self.screen.addstr(index + 1, 0, '', curses.A_DIM)
                continue
            elif bartype is Bar.NONE:
                for i, name in enumerate(bar.name.split('\n')):
                    self.screen.addstr((self.lines // 2) + i, (self.cols // 2) - len(name) // 2, name, curses.A_DIM)
                break

            # hightlight lines from same bar
            same = []
            for i, v in enumerate(self.data[top:bottom]):
                if v[0] is self.data[self.top_line_num + self.focus_line_num][0]:
                    same.append(v[0])

            tree = ' '
            if bar.owner == -1 and bar.owned > bar.channels:
                tree = ' │'
            if bar.owner != -1:
                tree = ' │'
            if bartype == Bar.LEFT:
                if bar.owner == -1:
                    tree = ' '
                if bar.owner != -1:
                    tree = ' ├─'
                    if bar.stream_index == bar.owned:
                        tree = ' └─'
                if bar.channels != 1:
                    brackets = [CFG.style.bar_top_left, CFG.style.bar_top_right]
                else:
                    brackets = [CFG.style.bar_left_mono, CFG.style.bar_right_mono]
            elif bartype == bar.channels - 1:
                if bar.stream_index == bar.owned:
                    tree = ' '
                brackets = [CFG.style.bar_bottom_left, CFG.style.bar_bottom_right]
            else:
                if bar.stream_index == bar.owned:
                    tree = ' '
                brackets = ['├', '┤']

            # focus current lines
            focus_hl, bracket_hl, arrow, gradient = 0, 0, CFG.style.arrow, self.gradient
            if index == self.focus_line_num:
                focus_hl = bracket_hl = curses.A_BOLD
                arrow = CFG.style.arrow_focused
            elif bar in same:
                focus_hl = curses.A_BOLD
                if bar.locked:
                    bracket_hl = curses.A_BOLD
                    arrow = CFG.style.arrow_locked
            elif not bar.muted and self.color_mode != 2:
                gradient = self.gray_gradient

            # highlight chosen sink/source or muted
            if not self.change_mode_allowed and self.selected[0].owner == self.data[index][0].index:
                bracket_hl = self.green | bracket_hl
                if bar.muted:
                    focus_hl = focus_hl | self.muted_color
            elif bar.muted:
                bracket_hl = bracket_hl | self.red
                focus_hl = focus_hl | self.muted_color

            off = 6 * (self.cols // (43 if self.cols <= 60 else 25)) - len(tree)
            cols = self.cols - 31 - off - len(tree)
            vol = list(CFG.style.bar_off * (cols - (cols % 3 != 0)))
            n = int(len(vol) * bar.volume[bartype] / bar.maxsize)
            if bar.muted:
                vol[:n] = CFG.style.bar_on_muted * n
            else:
                vol[:n] = CFG.style.bar_on * n
            vol = ''.join(vol)
            if bartype is Bar.LEFT:
                if bar.pa.name in (self.server_info.default_sink_name, self.server_info.default_source_name):
                    tree = CFG.style.default_stream
                name = '{}{}'.format(bar.name, bar.media_name)
                if bar.media_name_wide and len(bar.name) + sum(bar.media_name_widths) > 20 + off:
                    to_remove, widths = 0, [1] * len(bar.name) + bar.media_name_widths
                    while sum(widths) > 20 + off:
                        widths.pop()
                        to_remove += 1
                    name = name[:-to_remove].strip() + '~'
                elif len(name) > 20 + off:
                    name = name[:20 + off].strip() + '~'
                line = '{:<{}}|{}\n {:<3}|{}\n '.format(name, 22 + off, focus_hl,
                                                        '' if type(bar.pa) is PulseCard else bar.volume[0],
                                                        focus_hl)
            elif bartype is Bar.RIGHT:
                line = '{:>{}}|{}\n {}|{}\n {:<3}|{}\n '.format(
                    '', 21 + off, self.red if bar.locked else curses.A_DIM,
                    '', self.red if bar.muted else curses.A_DIM,
                    bar.volume[bartype], focus_hl)
            else:
                line = '{:>{}}{:<3}|{}\n '.format('', 23 + off, bar.volume[bartype], focus_hl)
            if type(bar.pa) is PulseCard:
                volbar = '\n{}|0'.format(bar.pa.active_profile.description.decode()[:len(vol)])
                brackets = [' ', ' ']
            else:
                volbar = ''
                for i, v in enumerate(re.findall('.{{{}}}'.format((len(vol) // 3)), vol)):
                    volbar += '\n{}|{}'.format(v, gradient[i] | focus_hl)
            line += '{:>1}|{}\n{}|{}{}\n{}|{}\n{}|{}'.format(arrow, curses.A_BOLD,
                                                             brackets[0], bracket_hl,
                                                             volbar,
                                                             brackets[1], bracket_hl,
                                                             arrow, curses.A_BOLD)
            self.display_line(index + 1, tree + "|0\n" + line)
        self.display_line(self.lines + 1, self.info)
        self.screen.refresh()

    def get_mode_keys(self):
        return [re.compile(r'[()]|KEY_').sub('', curses.keyname(k[0]).decode('utf-8')) for k in [
                CFG.keys.mode1, CFG.keys.mode2, CFG.keys.mode3]]

    def display_helpwin(self):
        doc = (('j k   ↑ ↓',                        'Navigation'),
               ('h l   ← →',                        'Change volume'),
               ('H L   Shift←  Shift→',             'Change volume by 10'),
               ('1 2 3 .. 8 9 0',                   'Set volume to 10%-100%'),
               ('m',                                'Mute/Unmute'),
               ('Space',                            'Lock/Unlock channels'),
               ('Enter',                            'Context menu'),
               ('{} {} {}'.format(*self.mode_keys), 'Change modes'),
               ('Tab   Shift Tab',                  'Next/Previous mode'),
               ('Mouse click',                      'Select device or mode'),
               ('Mouse wheel',                      'Volume change'),
               ('Esc q',                            'Quit'))
        win_width, desc_maxlen = self.helpwin.getmaxyx()[1] - 4, max(len(x[1]) for x in doc)
        self.helpwin.erase()
        for i, s in enumerate(doc):
            self.helpwin.addstr(i + 1, 2, s[0] + ' ' * (win_width - desc_maxlen - len(s[0])) + s[1])
        self.helpwin.border()
        self.helpwin.refresh()

    def run_helpwin(self):
        if self.getch() in CFG.keys.quit:
            self.helpwin_show = False

    def resize_submenu(self):
        key = lambda x: len(x.split('|')[0])
        self.submenu_width = min(self.cols + 1, max(30, len(max(self.submenu_data, key=key).split('|')[0]) + 3))
        self.submenu.resize(curses.LINES, self.submenu_width + 1)

    def display_submenu(self):
        top = self.top_line_num
        bottom = self.top_line_num + self.lines + 2
        self.submenu.erase()
        self.submenu.vline(0, self.submenu_width, curses.ACS_VLINE, curses.LINES)
        for index, line in enumerate(self.submenu_data[top:bottom]):
            if index == self.focus_line_num:
                focus_hl = curses.A_BOLD
                arrow = CFG.style.arrow_focused
            else:
                focus_hl = curses.A_NORMAL
                arrow = ' '
            if '|' in line:
                self.display_line(index, ' {}|0\n'.format(arrow) + line, focus_hl, win=self.submenu)
            else:
                self.submenu.addstr(index, 1, arrow + ' ' + line, focus_hl)
        self.submenu.refresh()

    def run_submenu(self):
        c = self.getch()
        if c in CFG.keys.quit:
            self.submenu_show = False
            self.focus_line_num = self.modes_data[5][1]
            self.top_line_num = self.modes_data[5][2]

        elif c in CFG.keys.up:
            self.scroll(self.UP, cycle=True)
        elif c in CFG.keys.down:
            self.scroll(self.DOWN, cycle=True)
        elif c in CFG.keys.top:
            self.scroll_first()
        elif c in CFG.keys.bottom:
            self.scroll_last()

        elif c == ord('\n'):
            focus = self.focus_line_num + self.top_line_num
            self.action = self.submenu_data[focus]
            if self.action == 'Move':
                if self.active_mode == 0:
                    self.change_mode(3)
                elif self.active_mode == 1:
                    self.change_mode(4)
                self.change_mode_allowed = self.submenu_show = False
                return
            elif self.action == 'Kill':
                try:
                    PULSE.kill_client(self.selected[0].pa.client.index)
                except:
                    if type(self.selected[0].pa) is PulseSinkInputInfo:
                        PULSE.kill_sink(self.selected[2])
                    else:
                        PULSE.kill_source(self.selected[2])
            elif self.action == 'Suspend':
                if type(self.selected[0].pa) is PulseSinkInfo:
                    PULSE.sink_suspend(self.selected[2], 1)
                else:
                    PULSE.source_suspend(self.selected[2], 1)
            elif self.action == 'Resume':
                if type(self.selected[0].pa) is PulseSinkInfo:
                    PULSE.sink_suspend(self.selected[2], 0)
                else:
                    PULSE.source_suspend(self.selected[2], 0)
            elif self.action == 'Set as default':
                if type(self.selected[0].pa) is PulseSinkInfo:
                    PULSE.set_default_sink(self.selected[0].pa.name)
                else:
                    PULSE.set_default_source(self.selected[0].pa.name)
            elif self.action == 'Set port':
                self.fill_submenu_pa(target='port', off=1, hide=CFG.ui.hide_unavailable_ports)
                self.focus_line_num = self.top_line_num = 0
                self.n_lines = len(self.submenu_data)
                return
            else:
                index = self.selected[0].pa.index
                description = self.action.rsplit('|')[0].strip()
                get_name = lambda desc, l: next(filter(lambda x: x.description.decode() == desc, l)).name
                if type(self.selected[0].pa) is PulseSinkInfo:
                    PULSE.set_sink_port(index, get_name(description, self.selected[0].pa.ports))
                elif type(self.selected[0].pa) is PulseSourceInfo:
                    PULSE.set_source_port(index, get_name(description, self.selected[0].pa.ports))
                elif type(self.selected[0].pa) is PulseCard:
                    PULSE.set_card_profile(index, get_name(description, self.selected[0].pa.profiles))
            self.change_mode_allowed = True
            self.submenu_show = False
            self.focus_line_num = self.modes_data[5][1]
            self.top_line_num = self.modes_data[5][2]

    def scroll(self, n, cycle=False):
        next_line_num = self.focus_line_num + n

        if n == self.UP and self.focus_line_num == 0 and self.top_line_num != 0:
            self.top_line_num += self.UP
            return
        elif n == self.DOWN and next_line_num == self.lines and (self.top_line_num + self.lines) != self.n_lines:
            self.top_line_num += self.DOWN
            return

        if n == self.UP:
            if self.top_line_num != 0 or self.focus_line_num != 0:
                self.focus_line_num = next_line_num
            elif cycle:
                self.scroll_last()
        elif n == self.DOWN and self.focus_line_num != self.lines:
            if self.top_line_num + self.focus_line_num + 1 != self.n_lines:
                self.focus_line_num = next_line_num
            elif cycle:
                self.scroll_first()

    def scroll_first(self):
        for _ in range(self.n_lines): self.scroll(self.UP)

    def scroll_last(self):
        for _ in range(self.n_lines): self.scroll(self.DOWN)


class Config():

    def __init__(self):

        class General:
            step = 1
            step_big = 10
            server = None

        self._more_keys = {'KEY_ESC': 27, 'KEY_TAB': 9, 'C': -96, 'M': 128}
        class Keys:
            up          = [ord('k'), curses.KEY_UP, curses.KEY_PPAGE]
            down        = [ord('j'), curses.KEY_DOWN, curses.KEY_NPAGE]
            left        = [ord('h'), curses.KEY_LEFT]
            right       = [ord('l'), curses.KEY_RIGHT]
            left_big    = [ord('H'), curses.KEY_SLEFT]
            right_big   = [ord('L'), curses.KEY_SRIGHT]
            top         = [ord('g'), curses.KEY_HOME]
            bottom      = [ord('G'), curses.KEY_END]
            mode1       = [curses.KEY_F1]
            mode2       = [curses.KEY_F2]
            mode3       = [curses.KEY_F3]
            next_mode   = [self._more_keys['KEY_TAB']]
            prev_mode   = [curses.KEY_BTAB]
            mute        = [ord('m')]
            lock        = [ord(' ')]
            quit        = [ord('q'), self._more_keys['KEY_ESC']]

        class UI:
            hide_unavailable_profiles = False
            hide_unavailable_ports = False
            color = 2
            mouse = True

        class Style:
            _bar_style = os.getenv('PULSEMIXER_BAR_STYLE', '┌╶┐╴└┘▮▯- ──').ljust(12, '?')
            bar_top_left       = _bar_style[0]
            bar_left_mono      = _bar_style[1]
            bar_top_right      = _bar_style[2]
            bar_right_mono     = _bar_style[3]
            bar_bottom_left    = _bar_style[4]
            bar_bottom_right   = _bar_style[5]
            bar_on             = _bar_style[6]
            bar_on_muted       = _bar_style[7]
            bar_off            = _bar_style[8]
            arrow              = _bar_style[9]
            arrow_focused      = _bar_style[10]
            arrow_locked       = _bar_style[11]
            default_stream     = '*'
            info_locked        = 'L'
            info_unlocked      = 'U'
            info_muted         = 'M'
            info_unmuted       = 'M'

        self.general = General()
        self.keys = Keys()
        self.ui = UI()
        self.style = Style()
        self.renames = {}
        self.path = os.getenv("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")) + '/pulsemixer.cfg'

    def save(self):
        default = '''
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
        ; bar-top-left       = ┌
        ; bar-left-mono      = ╶
        ; bar-top-right      = ┐
        ; bar-right-mono     = ╴
        ; bar-bottom-left    = └
        ; bar-bottom-right   = ┘
        ; bar-on             = ▮
        ; bar-on-muted       = ▯
        ; bar-off            = -
        ; arrow              = ' '
        ; arrow-focused      = ─
        ; arrow-locked       = ─
        ; default-stream     = *
        ; info-locked        = L
        ; info-unlocked      = U
        ; info-muted         = M  ; 🔇
        ; info-unmuted       = M  ; 🔉

        [renames]
        ;; Changes stream names in interactive mode, regular expression are supported
        ;; https://docs.python.org/3/library/re.html#regular-expression-syntax
        ; 'default name example' = 'new name'
        ; '(?i)built-in .* audio' = 'Audio Controller'
        ; 'AudioIPC Server' = 'Firefox'
        '''
        directory = self.path.rsplit('/', 1)[0]
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(self.path, 'w') as configfile:
            configfile.write(dedent(default).strip())
        return self.path

    def load(self):
        parser = ConfigParser(inline_comment_prefixes=('#', ';'), empty_lines_in_values=False)
        parser.optionxform = str  # keep case of keys, lowered() later
        parser.NONSPACECRE = re.compile(r"")  # ignore leading whitespace
        if not parser.read(self.path): return self
        if parser.has_section('renames'):
            self.renames = {re.compile(k.strip('"\'') + r'\Z'):v.strip('"\'') for k, v in parser.items('renames')}
            parser.remove_section('renames')
        def getkeys(s, k):
            keys = []
            for i in parser.get(s, k).strip(',').split(','):
                i = i.strip().strip('"\'')  # in case 'key' is encountered
                if len(i) > 1:
                    if i.startswith(('C-', 'M-')):
                        mod, key = i.split('-')
                        key = self._more_keys[mod] + ord(key.lower())
                    else:
                        key = getattr(curses, i, self._more_keys.get(i))
                else:
                    key = ord(i)
                if key is None: raise Exception("module 'curses' has no attribute {}".format(i))
                keys.append(key)
            return keys
        get = {str: lambda s, k: parser.get(s, k).strip('"\''),
               None.__class__: lambda s, k: parser.get(s, k).encode(),  # server
               list: getkeys, bool: parser.getboolean,
               int: parser.getint, float: parser.getfloat}
        for section in parser.sections():
            for key in parser[section]:
                pykey = key.lower().replace('-', '_')
                pyval = getattr(getattr(self, section.lower()), pykey)
                val = get[type(pyval)](section, key)
                setattr(getattr(self, section.lower()), pykey, val)
        return self


PULSE = CFG = None


def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "hvl",
            ["help", "version", "list", "list-sinks", "list-sources", "id=",
             "set-volume=", "set-volume-all=", "change-volume=", "max-volume=",
             "get-mute", "toggle-mute", "mute", "unmute", "get-volume",
             "color=", "server=", "no-mouse", "create-config"])
    except getopt.GetoptError as e:
        sys.exit("ERR: {}".format(e))
    assert args == [], sys.exit('ERR: {} not not recognized'.format(' '.join(args).strip()))
    dopts = dict(opts)

    if '-h' in dopts or '--help' in dopts:
        sys.exit(print(__doc__))
    if '-v' in dopts or '--version' in dopts:
        sys.exit(print(VERSION))
    if '--create-config' in dopts:
        try:
            sys.exit(print(Config().save()))
        except Exception as e:  # permission denied and such
            sys.exit('ERR: {}'.format(e))

    global PULSE, CFG
    try:
        CFG = Config().load()
    except Exception as e:
        sys.exit('ERR: {}'.format(e))
    CFG.general.server = dopts.get('--server', '').encode() or CFG.general.server
    CFG.ui.mouse = False if '--no-mouse' in dopts else CFG.ui.mouse
    try:
        CFG.ui.color = min(2, max(0, int(dopts.get('--color', '') or CFG.ui.color)))
    except:
        sys.exit('ERR: color must be a number')
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(1))
    PULSE = Pulse('pulsemixer', CFG.general.server)

    noninteractive_opts = dict(dopts)
    noninteractive_opts.pop('--server', None)
    noninteractive_opts.pop('--color', None)
    noninteractive_opts.pop('--no-mouse', None)
    if not noninteractive_opts:
        if not sys.stdout.isatty(): sys.exit('ERR: output is not a tty-like device')
        title = 'pulsemixer {}'.format(CFG.general.server.decode() if CFG.general.server else '')
        print('\033]2;{}\007'.format(title.strip()), end='', flush=True)
        curses.wrapper(Screen(CFG.ui.color, CFG.ui.mouse).run)

    sinks = PULSE.sink_list()
    sink_inputs = PULSE.sink_input_list()
    sources = PULSE.source_list()
    source_outputs = PULSE.source_output_list()
    server_info = PULSE.get_server_info()
    streams = OrderedDict()
    for k, v in (('sink-', sinks), ('sink-input-', sink_inputs), ('source-', sources), ('source-output-', source_outputs)):
        for stream in v: streams[k + str(stream.index)] = stream

    check_n = lambda x, err: x.strip('+-').isdigit() or sys.exit('ERR: {} must be a number'.format(err))
    check_id = lambda x: x in streams or sys.exit('ERR: No such ID: ' + str(x))
    from_old_id = lambda index: next((k for k in streams if k.rsplit('-', 1)[-1] == index), index)
    print_default = lambda x, y: print(x == y and ', Default' or '')

    if '--id' in dopts:
        index = [i for i in opts if '--id' in i][0][1]
        if index.isdigit(): index = from_old_id(index)
    else:
        index = 'sink-{}'.format([s.index for s in sinks if s.name == server_info.default_sink_name][0])
    check_id(index)
    max_volume = 150

    for opt, arg in opts:
        if opt == '--id':
            index = arg
            if index.isdigit(): index = from_old_id(index)
            check_id(index)
            max_volume = 150  # reset for each new id

        elif opt in ('-l', '--list'):
            for sink in sinks:
                print("Sink:\t\t", sink, end='')
                print_default(sink.name, server_info.default_sink_name)
            for sink in sink_inputs:
                print("Sink input:\t", sink)
            for source in sources:
                print("Source:\t\t", source, end='')
                print_default(source.name, server_info.default_source_name)
            for source in source_outputs:
                print("Source output:\t", source)

        elif opt == '--list-sinks':
            for sink in sinks:
                print("Sink:\t\t", sink, end='')
                print_default(sink.name, server_info.default_sink_name)
            for sink in sink_inputs:
                print("Sink input:\t", sink)

        elif opt == '--list-sources':
            for source in sources:
                print("Source:\t\t", source, end='')
                print_default(source.name, server_info.default_source_name)
            for source in source_outputs:
                print("Source output:\t", source)

        elif opt == '--get-mute':
            print(streams[index].mute)

        elif opt == '--mute':
            PULSE.mute_stream(streams[index])

        elif opt == '--unmute':
            PULSE.unmute_stream(streams[index])

        elif opt == '--toggle-mute':
            PULSE.unmute_stream(streams[index]) if streams[index].mute else PULSE.mute_stream(streams[index])

        elif opt == '--get-volume':
            print(*streams[index].volume.values)

        elif opt == '--set-volume':
            check_n(arg, err='volume')
            vol = streams[index].volume
            for i, _ in enumerate(vol.values):
                vol.values[i] = int(arg)
            PULSE.set_volume(streams[index], vol)

        elif opt == '--set-volume-all':
            vol = streams[index].volume
            arg = arg.strip(':').split(':')
            if len(arg) != len(vol.values):
                sys.exit("ERR: Specified volumes not equal to the number of channels in the stream")
            for i, _ in enumerate(vol.values):
                check_n(arg[i], err='volume')
                vol.values[i] = int(arg[i])
            PULSE.set_volume(streams[index], vol)

        elif opt == '--change-volume':
            check_n(arg, err='volume')
            vol = streams[index].volume
            for i, _ in enumerate(vol.values):
                vol.values[i] = min(vol.values[i] + int(arg), max_volume)
            PULSE.set_volume(streams[index], vol)

        elif opt == '--max-volume':
            check_n(arg, err='max volume')
            max_volume = int(arg)
            vol = streams[index].volume
            for i, _ in enumerate(vol.values):
                vol.values[i] = min(vol.values[i], max_volume)
            PULSE.set_volume(streams[index], vol)


if __name__ == '__main__':
    main()
