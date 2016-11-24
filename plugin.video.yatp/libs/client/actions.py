# coding: utf-8
# Module: actions
# Created on: 27.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import xbmcgui
import xbmcplugin
from simpleplugin import Plugin
import json_requests as jsonrq
from buffering import buffer_torrent, stream_torrent, add_torrent, get_videofiles

plugin = Plugin()
_ = plugin.initialize_gettext()
icons = os.path.join(plugin.path, 'resources', 'icons')
commands = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commands.py')


def _play(path):
    """
    Play a videofile

    :param path:
    :return:
    """
    plugin.log_notice('Path to play: {0}'.format(path))
    success = True if path else False
    return plugin.resolve_url(path, succeeded=success)


@plugin.action()
def root(params):
    """
    Plugin root

    :param params:
    :return:
    """
    return [{'label': _('Play .torrent file...'),
             'thumb': os.path.join(icons, 'play.png'),
             'url': plugin.get_url(action='select_torrent', target='play')},
            {'label': _('Download torrent from .torrent file...'),
             'thumb': os.path.join(icons, 'down.png'),
             'url': plugin.get_url(action='select_torrent', target='download'),
             'is_folder': False},
            {'label': _('Torrents'),
             'thumb': plugin.icon,
             'url': plugin.get_url(action='torrents')}]


@plugin.action()
def select_torrent(params):
    """
    Select .torrent file to play

    :param params:
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, _('Select .torrent file'), 'video', mask='.torrent')
    if torrent:
        plugin.log_notice('Torrent selected: {0}'.format(torrent))
        if params['target'] == 'play':
            return list_files({'torrent': torrent})
        else:
            download_torrent({'torrent': torrent})


@plugin.action('play')
def play_torrent(params):
    """
    Play torrent

    :param params:
    :return:
    """
    file_index = params.get('file_index')
    if file_index is not None and file_index != 'dialog':
        file_index = int(file_index)
    return _play(buffer_torrent(params['torrent'], file_index))


@plugin.action()
def play_file(params):
    """
    Stream a file from torrent by its index

    The torrent must be already added to the session!

    :param params:
    :return:
    """
    return _play(stream_torrent(int(params['file_index']), params['info_hash']))


@plugin.action('download')
def download_torrent(params):
    """
    Add torrent for downloading

    :param params:
    :return:
    """
    jsonrq.add_torrent(params['torrent'], False)
    xbmcgui.Dialog().notification('YATP', _('Torrent added for downloading'), plugin.icon, 3000)


@plugin.action()
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
                'url': plugin.get_url(action='show_files', info_hash=torrent['info_hash']),
                'is_folder': True}
        if torrent['state'] == 'downloading':
            item['thumb'] = os.path.join(icons, 'down.png')
        elif torrent['state'] == 'seeding':
            item['thumb'] = os.path.join(icons, 'up.png')
        elif torrent['state'] == 'paused':
            item['thumb'] = os.path.join(icons, 'pause.png')
        else:
            item['thumb'] = os.path.join(icons, 'question.png')
        context_menu = [(_('Pause all torrents'),
                         'RunScript({commands},pause_all)'.format(commands=commands)),
                        (_('Resume all torrents'),
                        'RunScript({commands},resume_all)'.format(commands=commands)),
                        (_('Delete torrent'),
                         'RunScript({commands},delete,{info_hash})'.format(commands=commands,
                                                                           info_hash=torrent['info_hash'])),
                        (_('Delete torrent and files'),
                         'RunScript({commands},delete_with_files,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])),
                        (_('Complete download'),
                         'RunScript({commands},restore_finished,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])),
                        (_('Torrent info'),
                         'RunScript({commands},show_info,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])),
                        ]
        if torrent['state'] == 'paused':
            context_menu.insert(0, (_('Resume torrent'),
                                    'RunScript({commands},resume,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])))
        else:
            context_menu.insert(0, (_('Pause torrent'),
                                    'RunScript({commands},pause,{info_hash})'.format(commands=commands,
                                                                                      info_hash=torrent['info_hash'])))
        item['context_menu'] = context_menu
        listing.append(item)
    return listing


@plugin.action()
def list_files(params):
    """
    Add a torrent to the session and display the list of files in a torrent

    :param params:
    :return:
    """
    torrent_data = add_torrent(params['torrent'])
    if torrent_data is not None:
        return _build_file_list(torrent_data['files'], torrent_data['info_hash'])
    else:
        xbmcgui.Dialog().notification(plugin.id, _('Playback cancelled.'), plugin.icon, 3000)
    return []


@plugin.action()
def show_files(params):
    """
    Display the list of videofiles

    :param params:
    :return:
    """
    return _build_file_list(jsonrq.get_files(params['info_hash']), params['info_hash'])


def _build_file_list(files, info_hash):
    """
    Create the list of videofiles in a torrent

    :param files:
    :param info_hash:
    :return:
    """
    videofiles = get_videofiles(files)
    listing = []
    for file_ in videofiles:
        ext = os.path.splitext(file_[1].lower())[1]
        if ext == '.avi':
            thumb = os.path.join(icons, 'avi.png')
        elif ext == '.mp4':
            thumb = os.path.join(icons, 'mp4.png')
        elif ext == '.mkv':
            thumb = os.path.join(icons, 'mkv.png')
        elif ext == '.mov':
            thumb = os.path.join(icons, 'mov.png')
        else:
            thumb = os.path.join(icons, 'play.png')
        listing.append({'label': '{name} [{size}{unit}]'.format(name=file_[1].encode('utf-8'),
                                                                size=file_[2] / 1048576,
                                                                unit=_('MB')),
                        'thumb': thumb,
                        'url': plugin.get_url(action='play_file',
                                              info_hash=info_hash,
                                              file_index=file_[0]),
                        'is_playable': True,
                        'info': {'video': {'size': file_[2]}},
                        })
    return plugin.create_listing(listing, cache_to_disk=True, sort_methods=(xbmcplugin.SORT_METHOD_LABEL,
                                                                            xbmcplugin.SORT_METHOD_SIZE))
