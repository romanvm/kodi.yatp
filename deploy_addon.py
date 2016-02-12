#!/usr/bin/env python
# coding: utf-8
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua

from __future__ import print_function
import re
import os
import shutil
import argparse
from subprocess import call

gh_token = os.environ['GH_TOKEN']
devnull = open(os.devnull, 'w')


def execute(args, silent=False):
    if silent:
        stdout = stderr = devnull
    else:
        stdout = stderr = None
    res = call(args, stdout=stdout, stderr=stderr)
    if res:
        raise RuntimeError('Call {call} returned error code {res}'.format(
            call=str(args).replace(gh_token, '*****'),
            res=res))


parser = argparse.ArgumentParser(
    description='Deploy an addon to my Kodi repo and/or publish docs on GitHub Pages')
parser.add_argument('-r', '--repo', help='push to my Kodi repo', action='store_true')
parser.add_argument('-d', '--docs', help='publish docs to GH pages', action='store_true')
args = parser.parse_args()

addon = os.environ['ADDON']
repo_slug= os.environ['TRAVIS_REPO_SLUG']
root_dir = os.path.dirname(os.path.abspath(__file__))
docs_dir = os.path.join(root_dir, 'docs')
html_dir = os.path.join(docs_dir, '_build', 'html')
gh_repo_url = 'https://{gh_token}@github.com/{repo_slug}.git'.format(gh_token=gh_token,
                                                                     repo_slug=repo_slug)
kodi_repo_dir = os.path.join(root_dir, 'kodi_repo')
kodi_repo_url = 'https://{gh_token}@github.com/romanvm/kodi_repo.git'.format(gh_token=gh_token)
os.chdir(root_dir)
with open(os.path.join(root_dir, addon, 'addon.xml'), 'rb') as addon_xml:
    version = re.search(r'(?<!xml )version="(.+?)"', addon_xml.read()).group(1)
if args.repo:
    shutil.make_archive('{0}-{1}'.format(addon, version),
                        'zip',
                        root_dir=root_dir,
                        base_dir=addon)
    print('ZIP created successfully.')
    execute(['git', 'clone', kodi_repo_url], silent=True)
    os.chdir(kodi_repo_dir)
    execute(['git', 'checkout', 'gh-pages'])
    execute(['git', 'config', 'user.name', '"Roman Miroshnychenko"'])
    execute(['git', 'config', 'user.email', '"romanvm@yandex.ua"'])
    shutil.copy(os.path.join(root_dir, addon, 'addon.xml'),
                os.path.join(kodi_repo_dir, 'repo', addon))
    shutil.copy(os.path.join(root_dir, '{0}-{1}.zip'.format(addon, version)),
                os.path.join(kodi_repo_dir, 'repo', addon))
    os.chdir(os.path.join(kodi_repo_dir, 'repo'))
    execute(['python', '@generate.py'])
    os.chdir(kodi_repo_dir)
    execute(['git', 'add', '--all', '.'])
    execute(['git', 'commit', '-m', '"Updates {addon} to v.{version}"'.format(addon=addon,
                                                                              version=version)])
    execute(['git', 'push', '--quiet'], silent=True)
    print('Addon {addon} v{version} deployed to my Kodi repo'.format(addon=addon,
                                                                     version=version))
if args.docs:
    os.chdir(docs_dir)
    execute(['make', 'html'])
    os.chdir(html_dir)
    execute(['git', 'init'])
    execute(['git', 'config', 'user.name', '"Roman Miroshnychenko"'])
    execute(['git', 'config', 'user.email', '"romanvm@yandex.ua"'])
    open('.nojekyll', 'w').close()
    execute(['git', 'add', '--all', '.'])
    execute(['git', 'commit', '-m' '"Updates {addon} docs to v.{version}"'.format(addon=addon,
                                                                                  version=version)])
    execute(['git', 'push', '--force', '--quiet', gh_repo_url, 'HEAD:gh-pages'], silent=True)
    print('{addon} docs v.{version} published to GitHub Pages.'.format(addon=addon,
                                                                       version=version))
