# Yet Anoter Torrent Player

Yet Anoter Torrent Player (YATP) is a torrent streaming video plugin for [Kodi](http://kodi.tv) mediacenter.
It allows to watch video torrents in Kodi without fully downloading them. The plugin can also act as a simple
torrent-client.

**Main features:**

- Video torrents playback in Kodi.
- Seeding after playback.
- Speed, ratio and time limits for torrents.
- Support for multi-file torrents - you can select individual video files for playback.
- Support for magnet links, local and remote .torrent files.
- Support for jump/seek to arbitrary parts of the video (it re-prioritizes pieces for download).

**Warning!** To use YATP you need a binary compiled libtorrent module which is not included in the plugin.

**Warning2!** The plugin is in WIP state and is subject to constant changes. Proper working distributions
will be provided after it is more or less finished.
## Basic Usage
YATP can be invoked from another Kodi video plugin using the following URL:
```
plugin://plugin.video.yatp/?action=play&torrent=<url-encoded path to a .torrent file or a magnet link>
```
The respective list item must have its *'IsPlayable'* property set to *'true'*.

YATP also allows to play local .torrent files containing videos.
## Torrent Client
YATP can also be used as a simple torrent-client. It has 2 interfaces to control torrents: Kodi UI and Web UI.
The Kodi UI is available from Kodi and the Web UI can be opened using the following URL:
```
http://<Kodi hostname or IP>:8668
```
The Web UI support basic operations with torrents: adding torrents for download and pausing/resuming/deleting them.

**License:** [GPL v.3](http://www.gnu.org/licenses/gpl-3.0.en.html).

The plugin includes [Bottle](http://bottlepy.org/docs/dev/index.html) module which is licensed separately
by its author(-s).
