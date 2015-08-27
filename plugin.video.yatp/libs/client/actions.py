# coding: utf-8
# Module: actions
# Created on: 27.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import time
import xbmcgui
from simpleplugin import Plugin
import json_requests as jsonrq
from buffering import buffer_torrent, stream_torrent

plugin = Plugin()
string = plugin.get_localized_string
icons = os.path.join(plugin.path, 'resources', 'icons')
commands = os.path.join(os.path.dirname(__file__), 'commands.py')


def _play(path):
    """
    Play a videofile

    :param path:
    :return:
    """
    plugin.log('Path to play: {0}'.format(path))
    success = True if path else False
    return plugin.resolve_url(path, success)


def root(params):
    """
    Plugin root

    :param params:
    :return:
    """
    return [{'label': string(32000),
             'thumb': os.path.join(icons, 'play.png'),
             'url': plugin.get_url(action='select_torrent', target='play'),
             'is_playable': True},
            {'label': string(32001),
             'thumb': os.path.join(icons, 'down.png'),
             'url': plugin.get_url(action='select_torrent', target='download'),
             'is_folder': False},
            {'label': string(32002),
             'thumb': plugin.icon,
             'url': plugin.get_url(action='torrents')}]


def select_torrent(params):
    """
    Select .torrent file to play

    :param params:
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, string(32003), 'video', mask='.torrent')
    if torrent:
        plugin.log('Torrent selected: {0}'.format(torrent))
        if params['target'] == 'play':
            return play_torrent({'torrent': torrent})
        else:
            download_torrent({'torrent': torrent})


def play_torrent(params):
    """
    Play torrent

    :param params:
    :return:
    """
    return _play(buffer_torrent(params['torrent'], params.get('file_index')))


def play_file(params):
    """
    Stream a file from torrent by its index

    The torrent must be already added via JSON-RPC!
    :param params:
    :return:
    """
    return _play(stream_torrent(params['file_index']))


def download_torrent(params):
    """
    Add torrent for downloading

    :param params:
    :return:
    """
    download_dir = params.get('download_dir') or plugin.download_dir
    jsonrq.download_torrent(params['torrent'], download_dir)
    time.sleep(1.0)
    if jsonrq.check_torrent_added():
        xbmcgui.Dialog().notification('YATP', string(32004), plugin.icon, 3000)


def torrents(params):
    """
    Display the list of torrents in the session

    :param params:
    :return:
    """
    listing = []
    torrent_list = sorted(jsonrq.get_all_torrent_info(), key=lambda i: i['added_time'], reverse=True)
    for torrent in torrent_list:
        if torrent['state'] == 'downloading':
            label = u'[COLOR=red]{0}[/COLOR]'.format(torrent['name'])
        elif torrent['state'] == 'seeding':
            label = u'[COLOR=green]{0}[/COLOR]'.format(torrent['name'])
        elif torrent['state'] == 'paused':
            label = u'[COLOR=gray]{0}[/COLOR]'.format(torrent['name'])
        else:
            label = u'[COLOR=blue]{0}[/COLOR]'.format(torrent['name'])
        item = {'label': label,
                'url': plugin.get_url(action='torrent_info', info_hash=torrent['info_hash']),
                'is_folder': False}
        if torrent['state'] == 'downloading':
            item['thumb'] = os.path.join(icons, 'down.png')
        elif torrent['state'] == 'seeding':
            item['thumb'] = os.path.join(icons, 'up.png')
        elif torrent['state'] == 'paused':
            item['thumb'] = os.path.join(icons, 'pause.png')
        else:
            item['thumb'] = os.path.join(icons, 'question.png')
        listing.append(item)
        context_menu = [(string(32005),
                         'RunScript({commands},pause_all)'.format(commands=commands)),
                        (string(32006),
                        'RunScript({commands},resume_all)'.format(commands=commands)),
                        (string(32007),
                         'RunScript({commands},delete,{info_hash})'.format(commands=commands,
                                                                           info_hash=torrent['info_hash'])),
                        (string(32008),
                         'RunScript({commands},delete_with_files,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash']))]
        if torrent['state'] == 'paused':
            context_menu.insert(0, (string(32009),
                                    'RunScript({commands},resume,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])))
        else:
            context_menu.insert(0, (string(32010),
                                    'RunScript({commands},pause,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])))
        item['context_menu'] = (context_menu, True)
    return listing


def torrent_info(params):
    """
    Display current torrent info

    :param params:
    :return:
    """
    torr_info = jsonrq.get_torrent_info(params['info_hash'])
    info_dialog = xbmcgui.DialogProgress()
    info_dialog.create(torr_info['name'])
    while not info_dialog.iscanceled():
        info_dialog.update(torr_info['progress'],
                           string(32011).format(torr_info['size'],
                                           torr_info['state'],
                                           torr_info['num_seeds'],
                                           torr_info['num_peers']),
                           string(32012).format(torr_info['dl_speed'], torr_info['ul_speed']),
                           string(32013).format(torr_info['total_download'],
                                                                     torr_info['total_upload']))
        time.sleep(1.0)
        torr_info = jsonrq.get_torrent_info(params['info_hash'])


plugin.actions['root'] = root
plugin.actions['select_torrent'] = select_torrent
plugin.actions['play'] = play_torrent
plugin.actions['play_file'] = play_file
plugin.actions['download'] = download_torrent
plugin.actions['torrents'] = torrents
plugin.actions['torrent_info'] = torrent_info
