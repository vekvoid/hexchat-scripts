#!/usr/bin/env python3

import hexchat
import requests
import sys
import threading

__module_name__ = "Twitch Title"
__module_author__ = "Poorchop"
__module_version__ = "1.0"
__module_description__ = "Display stream status and description for TwitchTV streams"

t = None
twitch_chans = {}


def is_twitch():
    server = hexchat.get_info("server")
    if server and "twitch.tv" in server:
        return True
    else:
        return False


def set_topic(channel, display_name, status, game, title):
    global twitch_chans
    msg = "\00318{0}\00399 - {1} | Now playing: \00318{2}\00399 | {3}".format(display_name, status, game, title)
    stripped_msg = hexchat.strip(msg, -1, 3)
    if twitch_chans["#{}".format(channel)] != stripped_msg:
        twitch_chans["#{}".format(channel)] = stripped_msg
        print(msg)
        if sys.platform == "win32":
            # HexChat on Windows has poor support for colors in topic bar
            hexchat.command("RECV :{0}!Topic@twitch.tv TOPIC #{0} :{1}".format(channel, stripped_msg))
        else:
            hexchat.command("RECV :{0}!Topic@twitch.tv TOPIC #{0} :{1}".format(channel, msg))


def get_stream_info(channel):
    url = "https://api.twitch.tv/kraken/streams?"
    params = {"channel": channel}
    r = requests.get(url, params=params)
    data = r.json()
    display_name = channel
    game = ""
    title = "\035Stream is offline\017"
    if not data["streams"]:
        status = "\00320\002OFFLINE\002\00399"
    else:
        status = "\00319\002LIVE\002\00399"
        display_name = data["streams"][0]["channel"]["display_name"]
        game = data["streams"][0]["channel"]["game"]
        title = data["streams"][0]["channel"]["status"]
    set_topic(channel, display_name, status, game, title)


def update_status():
    global twitch_chans
    if twitch_chans:
        for chan in twitch_chans:
            channel = chan[1:]
            get_stream_info(channel)


def get_twitch_chans():
    global twitch_chans
    for chan in hexchat.get_list("channels"):
        if chan.type == 2 and chan.context.get_info("server") == "tmi.twitch.tv" and chan.channel not in twitch_chans:
            twitch_chans[chan.channel] = ""


def unload_cb(userdata):
    """
    Prevent HexChat from crashing while a thread is active
    """
    global t
    t.cancel()
    t.join()
    t = None


def channel_check():
    """
    Check to see if there are any open Twitch channels; if so, then start/continue the threaded process
    """
    for chan in hexchat.get_list("channels"):
        if chan.type == 2 and chan.context.get_info("server") == "tmi.twitch.tv":
            return True
        else:
            return False


def get_current_status():
    """
    Update the stream status every 10 minutes
    """
    global t
    if channel_check():
        get_twitch_chans()
        update_status()
        t = threading.Timer(600, get_current_status)
        t.daemon = True
        t.start()


get_current_status()
hexchat.hook_unload(unload_cb)

print(__module_name__ + " version " + __module_version__ + " loaded")
