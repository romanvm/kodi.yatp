# -*- coding: utf-8 -*-
# Module: simpleplugin
# Author: Roman V.M.
# Created on: 03.06.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
SimplePlugin micro-framework for Kodi content plugins

License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""

import os
import sys
import re
from datetime import datetime, timedelta
from cPickle import dump, load, PickleError
from urlparse import parse_qs
from urllib import urlencode
import xbmcaddon
import xbmc
import xbmcplugin
import xbmcgui


class PluginError(Exception):
    """Custom exception"""
    pass


class Storage(object):
    """
    Persistent storage for arbitrary data with a dictionary-like interface

    It is designed as a context manager and better be used
    with 'with' statement.
    Usage:

    with Storage('c:\\storage\\') as storage:
        storage[key1] = value1
        value2 = storage[key2]

    """
    def __init__(self, storage_dir, filename='storage.pcl'):
        """
        Class constructor

        :param storage_dir: str - directory for storage
        :param filename: str - the name of a storage file
        :return:
        """
        self._storage = {}
        filename = os.path.join(storage_dir, filename)
        if os.path.exists(filename):
            mode = 'r+b'
        else:
            mode = 'w+b'
        self._file = open(filename, mode)
        try:
            self._storage = load(self._file)
        except (PickleError, EOFError):
            pass

    def __enter__(self):
        """Create context manager"""
        return self

    def __exit__(self, *args):
        """Clean up context manager"""
        self.flush()
        return False

    def __getitem__(self, key):
        return self._storage[key]

    def __setitem__(self, key, value):
        self._storage[key] = value

    def __delitem__(self, key):
        del self._storage[key]

    def __contains__(self, item):
        return item in self._storage

    def __iter__(self):
        return self.iterkeys()

    def get(self, key, default=None):
        return self._storage.get(key, default)

    def iteritems(self):
        return self._storage.iteritems()

    def iterkeys(self):
        return self._storage.iterkeys()

    def itervalues(self):
        return self._storage.itervalues()

    def keys(self):
        return self._storage.keys()

    def values(self):
        return self._storage.values()

    def flush(self):
        """
        Flush storage to disk

        This method invalidates a Storage instance.
        :return:
        """
        self._file.seek(0)
        dump(self._storage, self._file)
        self._file.truncate()
        self._file.close()
        del self._file
        del self._storage


class Addon(object):
    """
    Base addon class

    Provides access to basic addon parameters
    """
    def __init__(self, id_=''):
        """Class constructor"""
        self._addon = xbmcaddon.Addon(id_)
        self._configdir = xbmc.translatePath('special://profile/addon_data/{0}'.format(self.id)).decode('utf-8')
        if not os.path.exists(self._configdir):
            os.mkdir(self._configdir)

    def __getattr__(self, item):
        """
        Get addon setting as an Addon instance attribute

        E.g. addon.my_setting is equal to addon.get_setting('my_setting')
        :param item:
        :return:
        """
        return self.get_setting(item)

    @property
    def addon(self):
        """
        Kodi Addon instance that represents this Addon

        :return: Addon instance
        """
        return self._addon

    @property
    def id(self):
        """
        Addon ID

        :return: str, e.g. 'plugin.video.foo'
        """
        return self._addon.getAddonInfo('id')

    @property
    def path(self):
        """
        Addon path

        :return: str
        """
        return self._addon.getAddonInfo('path').decode('utf-8')

    @property
    def icon(self):
        """
        Addon icon

        :return: str
        """
        icon = os.path.join(self.path, 'icon.png')
        if os.path.exists(icon):
            return icon
        else:
            return ''

    @property
    def fanart(self):
        """
        Addon fanart

        :return: str
        """
        fanart = os.path.join(self.path, 'fanart.jpg')
        if os.path.exists(fanart):
            return fanart
        else:
            return ''

    @property
    def config_dir(self):
        """
        Addon config dir

        :return: str
        """
        return self._configdir

    def get_localized_string(self, id_):
        """
        Get localized UI string

        :param id_: int - UI string ID
        :return: str - UI string in current language
        """
        return self._addon.getLocalizedString(id_).encode('utf-8')

    def get_setting(self, id_, convert=True):
        """
        Get addon setting

        If convert=True, 'bool' settings are converted to Python bool values,
        and numeric strings to Python long or float depending on their format.

        :param id_: str - setting ID
        :param convert: bool - try to guess and convert the setting to an appropriate type
            E.g. '1.0' will be converted to float 1.0 number, 'true' to True and so on.
        :return: setting value
        """
        setting = self._addon.getSetting(id_)
        if convert:
            if setting == 'true':
                return True  # Convert boolean strings to bool
            elif setting == 'false':
                return False
            elif re.search(r'^\d+$', setting) is not None:
                return long(setting)  # Convert numeric strings to long
            elif re.search(r'^\d+\.\d+$', setting) is not None:
                return float(setting)  # Convert numeric strings with a dot to float
        return setting

    def set_setting(self, id_, value):
        """
        Set addon setting

        Python bool type are converted to 'true' or 'false'
        Non-string/non-unicode values are converted to strings.

        :param id_: str - setting ID
        :param value: - setting value
        :return:
        """
        if isinstance(value, bool):
            value = 'true' if value else 'false'
        elif not isinstance(value, (str, unicode)):
            value = str(value)
        self._addon.setSetting(id_, value)

    def log(self, message, level=xbmc.LOGNOTICE):
        """
        Add message to Kodi log starting with Addon ID

        :param message: str
        :param level: int - log level
        :return:
        """
        xbmc.log('{0}: {1}'.format(self.id, message), level)

    def get_storage(self, filename='storage.pcl'):
        """
        Get a persistent Storage instance for storing arbitrary values between addon calls.

        A Storage instance can be used as a context manager.
        Example:
        =====================================
        with plugin.get_storage() as storage:
            storage['param1'] = value1
            value2 = storage['param2']
        ...
        =====================================
        Note that after exiting 'with' block a Storage instance is invalidated.
        """
        return Storage(self.config_dir, filename)

    def cached(self, duration=10):
        """
        Cached decorator

        Used to cache function return data
        Usage:

        @cached(30)
        def my_func(*args, **kwargs):
            ...
            return value

        :param duration: int - cache time in min, negative value - cache indefinitely
        :return:
        """
        def outer_wrapper(func):
            def inner_wrapper(*args, **kwargs):
                with self.get_storage(filename='cache.pcl') as cache:
                    current_time = datetime.now()
                    key = func.__name__ + str(args) + str(kwargs)
                    try:
                        data, timestamp = cache[key]
                        if duration > 0 and current_time - timestamp > timedelta(minutes=duration):
                            raise KeyError
                    except KeyError:
                        data = func(*args, **kwargs)
                        cache[key] = (data, current_time)
                return data
            return inner_wrapper
        return outer_wrapper


class Plugin(Addon):
    """
    Plugin class

    It provides a simplified API to create virtual directories of playable items
    in Kodi content plugins.
    simpleplugin.Plugin uses a concept of callable plugin actions (functions or methods)
    that are mapped to 'action' parameters via actions instance property.
    A Plugin instance must have at least one action for its root section
    mapped to 'root' string.

    Minimal example:
    ===============================
    from simpleplugin import Plugin

    plugin = Plugin()

    def root_action(params):
        return [{'label': 'Foo',
                'url': plugin.get_url(action='some_action', param='Foo')},
                {'label': 'Bar',
                'url': plugin.get_url(action='some_action', param='Bar'}]

    def some_action(params):
        return [{'label': param['param']}]

    plugin.actions['root'] = root_action  # Mandatory item!
    plugin.actions['some_action'] = some_action
    plugin.run()
    ==============================

    IMPORTANT: You need to map function or method objects without round brackets!
    E.g.
    plugin.actions['some_action'] = some_action  # Correct :)
    plugin.actions['some_action'] = some_action()  # Wrong! :(

    An action callable receives 1 parameter - params.
    params is a dict containing plugin call parameters (including action string)
    The action callable can return
    either a list of dictionaries representing Kodi virtual directory items
    or a resolved playable path (str or unicode) for Kodi to play.

    Examples:
    ==============================
    def list_action(params):
        listing = get_listing(params)  # Some external function to create listing
        return listing
    ==============================
    def play_action(params):
        path = get_path(params)  # Some external function to get a playable path
        return path
    ==============================
    listing is a Python list of dict items.

    Each dict item can contain the following properties:

    label - item's label (default: '').
    label2 - item's label2 (default: '').
    thumb - item's thumbnail (default: '').
    icon - item's icon (default: '').
    fanart - item's fanart (optional).
    art - a dict containing all item's graphic (see ListItem.setArt for more info) - optional.
    stream_info - a dictionary of {stream_type: {param: value}} items (see ListItem.addStreamInfo) - optional.
    info -  a dictionary of {media: {param: value}} items (see ListItem.setInfo) - optional
    context_menu - a list or a tuple. A list must contain 2-item tuples ('Menu label', 'Action').
        If a list is provided then the items from the tuples are added to the item's context menu.
        Alternatively, context_menu can be a 2-item tuple. The 1-st item is a list as described above,
        and the 2-nd is a boolean value for replacing items. If True, context menu will contain only
        the provided items, if False - the items are added to an existing context menu.
        context_menu param is optional.
    url - a callback URL for this list item.
    is_playable - if True, then this item is playable and must return a playable path or
        be resolved via plugin.resolve_url() (default: False).
    is_folder - if True then the item will open a lower-level sub-listing. if False,
        the item either is a playable media or a general-purpose script
        which neither creates a virtual folder nor points to a playable media (default: True).
        if is_playable is set to True, then is_folder value automatically assumed to be False.
    subtitles - the list of paths to subtitle files (optional).
    mime - item's mime type (optional).
    Example:
    listing = [{    'label': 'Label',
                    'label2': 'Label 2',
                    'thumb': 'thumb.png',
                    'icon': 'icon.png',
                    'fanart': 'fanart.jpg',
                    'art': {'clearart': 'clearart.png'},
                    'stream_info': {'video': {'codec': 'h264', 'duration': 1200},
                                    'audio': {'codec': 'ac3', 'language': 'en'}},
                    'info': {'video': {'genre': 'Comedy', 'year': 2005}},
                    'context_menu': ([('Menu Item', 'Action')], True),
                    'url': 'plugin:/plugin.video.test/?action=play',
                    'is_playable': True,
                    'is_folder': False,
                    'subtitles': ['/path/to/subtitles.en.srt', '/path/to/subtitles.uk.srt'],
                    'mime': 'video/mp4'
                    }]

    Alternatively, an action callable can use Plugin.create_listing() and Plugin.resolve_url()
    static methods to set additional parameters for Kodi.

    Examples:
    ==============================
    def list_action(params):
        listing = get_listing(params)  # Some external function to create listing
        return Plugin.create_listing(listing, sort_methods=(2, 10, 17), view_mode=500)
    ==============================
    def play_action(params):
        path = get_path(params)  # Some external function to get a playable path
        return Plugin.resolve_url(path, succeeded=True)
    ==============================

    If an action callable performs any actions other than creating a listing or
    resolving a playable URL, it must return None.
    """
    def __init__(self, id_=''):
        """Class constructor"""
        super(Plugin, self).__init__(id_)
        self._url = 'plugin://{0}/'.format(self.id)
        self._handle = None
        self.actions = {}

    @staticmethod
    def get_params(paramstring):
        """
        Convert a URL-encoded paramstring to a Python dict

        :param paramstring: str
        :return: dict
        """
        params = parse_qs(paramstring)
        for key, value in params.iteritems():
            params[key] = value[0] if len(value) == 1 else value
        return params

    def get_url(self, plugin_url='', **kwargs):
        """
        Construct a callable URL for a virtual directory item

        If plugin_url is empty, a current plugin URL is used.
        kwargs are converted to a URL-encoded string of plugin call parameters
        To call a plugin action, 'action' parameter must be used,
        if 'action' parameter is missing, then the plugin root action is called
        If the action is not added to Plugin actions, PluginError will be raised.

        :param plugin_url: str - a plugin URL with trailing /
        :param kwargs: pairs if key=value items
        :return: str - a full plugin callback URL
        """
        url = plugin_url or self._url
        if kwargs:
            return '{0}?{1}'.format(url, urlencode(kwargs))
        return url

    def run(self, category=''):
        """
        Run plugin

        :param category: str - plugin sub-category, e.g. 'Comedy'.
            see xbmcplugin.setPluginCategory() for more info
        :return:
        """
        self._handle = int(sys.argv[1])
        if category:
            xbmcplugin.setPluginCategory(self._handle, category)
        params = self.get_params(sys.argv[2][1:])
        action = params.get('action', 'root')
        self.log('Actions: {0}'.format(str(self.actions.keys())))
        self.log('Called action "{0}" with params "{1}"'.format(action, str(params)))
        try:
            action_callable = self.actions[action]
        except KeyError:
            raise PluginError('Invalid action: "{0}"!'.format(action))
        else:
            result = action_callable(params)
            self.log('Action return value: {0}'.format(str(result)), xbmc.LOGDEBUG)
            if isinstance(result, list):
                self._create_listing(self.create_listing(result))
            elif isinstance(result, (str, unicode)):
                self._resolve_url(self.resolve_url(result))
            elif isinstance(result, dict) and result.get('listing') is not None:
                self._create_listing(result)
            elif isinstance(result, dict) and result.get('path') is not None:
                self._resolve_url(result)
            else:
                self.log('The action "{0}" has not returned any valid data to process.'.format(action), xbmc.LOGWARNING)

    @staticmethod
    def create_listing(listing, succeeded=True, update_listing=False, cache_to_disk=False, sort_methods=None,
                       view_mode=50, content=None):
        """
        Create and return a context dict for a virtual folder listing

        :param listing: list - the list of the plugin virtual folder items
        :param succeeded: bool - if False Kodi won't open a new listing and stays on the current level.
        :param update_listing: bool - if True, Kodi won't open a sub-listing but refresh the current one.
        :param cache_to_disk: bool
        :param sort_methods: tuple - the list of integer constants representing virtual folder sort methods.
        :param view_mode: int - a numeric code for a skin view mode.
            View mode codes are different in different skins except for 50 (basic listing).
        :param content: string - current plugin content, e.g. 'movies' or 'episodes'.
            See xbmcplugin.setContent() for more info.
        :return: dict - context dictionary containing necessary parameters
            to create virtual folder listing in Kodi UI.
        """
        return {'listing': listing, 'succeeded': succeeded, 'update_listing': update_listing,
                'cache_to_disk': cache_to_disk, 'sort_methods': sort_methods, 'view_mode': view_mode,
                'content': content}

    @staticmethod
    def resolve_url(path, succeeded=True):
        """
        Create and return a context dict to resolve a playable URL

        :param path: string or unicode - the path to a playable media.
        :param succeeded: bool - if False, Kodi won't play anything
        :return: dict - context dictionary containing necessary parameters
            for Kodi to play the selected media.
        """
        return {'path': path, 'succeeded': succeeded}

    def _create_listing(self, context):
        """
        Create a virtual folder listing

        :param context: dict - context dictionary
        :return:

        """
        self.log('Creating listing from {0}'.format(str(context)), xbmc.LOGDEBUG)
        if context.get('content'):
            xbmcplugin.setContent(self._handle, context['content'])
        listing = []
        for item in context['listing']:
            list_item = xbmcgui.ListItem(label=item.get('label', ''),
                                         label2=item.get('label2', ''),
                                         thumbnailImage=item.get('thumb', ''),
                                         iconImage=item.get('icon', ''))
            if item.get('fanart'):
                list_item.setProperty('fanart_image', item['fanart'])
            if item.get('art'):
                list_item.setArt(item['art'])
            if item.get('stream_info'):
                for stream, stream_info in item['stream_info'].iteritems():
                    list_item.addStreamInfo(stream, stream_info)
            if item.get('info'):
                for media, info in item['info'].iteritems():
                    list_item.setInfo(media, info)
            if item.get('context_menu') and isinstance(item['context_menu'], list):
                list_item.addContextMenuItems(item['context_menu'])
            elif item.get('context_menu') and isinstance(item['context_menu'], tuple):
                list_item.addContextMenuItems(item['context_menu'][0], item['context_menu'][1])
            if item.get('is_playable'):
                list_item.setProperty('IsPlayable', 'true')
                is_folder = False
            else:
                is_folder = item.get('is_folder', True)
            if item.get('subtitles'):
                list_item.setSubtitles(item['subtitles'])
            if item.get('mime'):
                list_item.setMimeType(item['mime'])
            listing.append((item['url'], list_item, is_folder))
        xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))
        if context['sort_methods'] is not None:
            [xbmcplugin.addSortMethod(self._handle, method) for method in context['sort_methods']]
        xbmcplugin.endOfDirectory(self._handle,
                                  context['succeeded'],
                                  context['update_listing'],
                                  context['cache_to_disk'])
        if context['view_mode'] != 50:
            xbmc.executebuiltin('Container.SetViewMode({0})'.format(context['view_mode']))

    def _resolve_url(self, context):
        """
        Resolve a playable URL

        :param context: dict
        :return:
        """
        self.log('Resolving URL from {0}'.format(str(context)), xbmc.LOGDEBUG)
        list_item = xbmcgui.ListItem(path=context['path'])
        xbmcplugin.setResolvedUrl(self._handle, context['succeeded'], list_item)
