# coding: utf-8
# Module: actions
# Created on: 27.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import time
import xbmcgui
from simpleplugin import Plugin
import json_requests as jsonrq
from buffering import buffer_torrent

plugin = Plugin()
icons = os.path.join(plugin.path, 'resources', 'icons')
commands = os.path.join(os.path.dirname(__file__), 'commands.py')


def root(params):
    """
    Plugin root

    :param params:
    :return:
    """
    return [{'label': 'Play .torrent file...',
             'thumb': os.path.join(icons, 'play.png'),
             'url': plugin.get_url(action='select_torrent', target='play'),
             'is_playable': True},
            {'label': 'Download torrent from .torrent file...',
             'thumb': os.path.join(icons, 'down.png'),
             'url': plugin.get_url(action='select_torrent', target='download'),
             'is_folder': False},
            {'label': 'Torrents',
             'thumb': plugin.icon,
             'url': plugin.get_url(action='torrents')}]


def select_torrent(params):
    """
    Select .torrent file to play

    :param params:
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file', 'video', mask='.torrent')
    if torrent:
        plugin.log('Torrent selected: {0}'.format(torrent))
        if params['target'] == 'play':
            play_torrent({'torrent': torrent})
        else:
            download_torrent({'torrent': torrent})


def play_torrent(params):
    """
    Play torrent

    :param params:
    :return:
    """
    path = buffer_torrent(params['torrent'])
    success = True if path else False
    return plugin.resolve_url(path, success)


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
        xbmcgui.Dialog().notification('YATP', 'Torrent added for downloading', plugin.icon, 3000)


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
            label = '[COLOR=red]{0}[/COLOR]'.format(torrent['name'])
        elif torrent['state'] == 'seeding':
            label = '[COLOR=green]{0}[/COLOR]'.format(torrent['name'])
        elif torrent['state'] == 'paused':
            label = '[COLOR=gray]{0}[/COLOR]'.format(torrent['name'])
        else:
            label = '[COLOR=blue]{0}[/COLOR]'.format(torrent['name'])
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
        context_menu = [('Pause all torrents',
                         'RunScript({commands},pause_all)'.format(commands=commands)),
                        ('Resume all torrents',
                        'RunScript({commands},resume_all)'.format(commands=commands)),
                        ('Delete torrent',
                         'RunScript({commands},delete,{info_hash})'.format(commands=commands,
                                                                           info_hash=torrent['info_hash'])),
                        ('Delete torrent and files',
                         'RunScript({commands},delete_with_files,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash']))]
        if torrent['state'] == 'paused':
            context_menu.insert(0, ('Resume torrent',
                                    'RunScript({commands},resume,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])))
        else:
            context_menu.insert(0, ('Pause torrent',
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
                           'size: {0}; state: {1}; seeds: {2}; peers: {3}'.format(torr_info['size'],
                                                                                  torr_info['state'],
                                                                                  torr_info['num_seeds'],
                                                                                  torr_info['num_peers']),
                           'DL speed: {0}KB/s; UL speed: {1}KB/s'.format(torr_info['dl_speed'], torr_info['ul_speed']),
                           'total DL: {0}MB; total UL: {1}MB'.format(torr_info['total_download'],
                                                                     torr_info['total_upload']))
        time.sleep(1.0)
        torr_info = jsonrq.get_torrent_info(params['info_hash'])


plugin.actions['root'] = root
plugin.actions['select_torrent'] = select_torrent
plugin.actions['play'] = play_torrent
plugin.actions['download'] = download_torrent
plugin.actions['torrents'] = torrents
plugin.actions['torrent_info'] = torrent_info
