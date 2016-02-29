# Contributing to YATP Project

You can help to improve YATP in various ways: by making feature requests or bug reports via the project's
issue tracker or by submitting pull requests with improvements and/or bugfixes.
When doing this please follow the simple rules described below.

## Bug Reports

Before submitting a bug report read carefully the [project's Wiki](https://github.com/romanvm/kodi.yatp/wiki)
to check if this is a known issue/feature.
When submitting bug reports you need to provide the following information:

1. Your system description and Kodi version.
2. Detailed description of the bug (not just "something does not work").
3. [Kodi debug log](http://kodi.wiki/view/Log_file/Easy) as a link to some pastebin site
  (for example, [XBMC Logs](http://xbmclogs.com/)).
  A Kodi debug log is mandatory, unless you are reporting a cosmetic bug in YATP UI.

## Feature Requests

When submitting a feature request provide an explanation why do you think this feature is important.
Please keep in mind that that I don't like the idea of bloating YATP with many features beyond reasonable minimum.
YATP has a rich API and additional features can be implemented in other plugins for Kodi.

Also I will never add the following features:

- Support for specific torrent sites. This is better be implemented in separate addons for Kodi.
- Features that facilitate torrent "hit-and-runnign", that is downloading a torrent without proper seeding.
  An example of such feature is deleting vileofiles immediately after watching them.
  Please seed your torrents for other users.

## Pull Requests

I have limited time and resources for YATP developement and will gladly accept any help.
If you are proficient in Python (or in HTML/CSS/JavaScript if you want to work on the web-UI)
and want to improve YATP, please submit pull requests through GitHub.

Note that `/site-packages` directory contains third-party Python libraries that are not a part of YATP.

A pull request should comply with simple rules:

- Python code must follow [PEP-8](https://www.python.org/dev/peps/pep-0008/) except for line length
  that can be increased to 120 characters.
- The code should be reasonably commented in docstrings and inline comments.
  If possible, use Sphinx-compatible docstrings with reStructuredText markup.
