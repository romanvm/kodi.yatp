# coding: utf-8
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua

from __future__ import print_function
import re
import os
import shutil
import argparse

parser = argparse.ArgumentParser(
    description='Deploy an addon to my Kodi repo and/or publish docs on GitHub Pages')
parser.add_argument('-r', '--repo', help='push to my Kodi repo', action='store_true')
parser.add_argument('-d', '--docs', help='publish docs to GH pages', action='store_true')
args = parser.parse_args()

addon = os.environ['ADDON']
gh_token = os.environ['GH_TOKEN']
root_dir = os.path.dirname(os.path.abspath(__file__))
docs_dir = os.path.join(root_dir, 'docs')
html_dir = os.path.join(docs_dir, '_build', 'html')
gh_repo_url = 'https://{gh_token}@github.com/{repo_slug}.git'.format(gh_token=gh_token,
                                                                     repo_slug=os.environ['TRAVIS_REPO_SLUG'])
kodi_repo_dir = os.path.join(root_dir, 'kodi_repo')
kodi_repo_url = 'https://{gh_token}@github.com/romanvm/kodi_repo.git'.format(gh_token=gh_token)
os.chdir(root_dir)
with open(os.path.join(root_dir, addon, 'addon.xml'), 'rb') as addon_xml:
    version = re.search(r'(?<!xml )version="(.+?)"', addon_xml.read()).group(1)
if args.repo:
    shutil.make_archive('{0}-{1}'.format(addon, version),
                        'zip',
                        root_dir=root_dir,
                        base_dir=os.path.join(root_dir, addon))
    print('ZIP created successfully.')
    os.system('git clone {url}'.format(url=kodi_repo_url))
    os.chdir(kodi_repo_dir)
    os.system('git checkout gh-pages')
    os.system('git pull')
    shutil.copy(os.path.join(root_dir, addon, 'addon.xml'),
                os.path.join(kodi_repo_dir, 'repo', addon))
    shutil.copy(os.path.join(root_dir, '{0}-{1}.zip'.format(addon, version)),
                os.path.join(kodi_repo_dir, 'repo', addon))
    os.chdir(os.path.join(kodi_repo_dir, 'repo'))
    os.system('python @generate.py')
    os.chdir(kodi_repo_dir)
    os.system('git add --all .')
    os.system('git commit -m "Updates {addon} to v.{version}"'.format(addon=addon,
                                                                      version=version))
    os.system('git push')
    print('Addon {0} v.{1} deployed to my Kodi repo'.format(addon, version))
if args.docs:
    os.chdir(docs_dir)
    os.system('make html')
    os.chdir(html_dir)
    os.system('git init')
    os.system('git config user.name "Roman Miroshnychenko"')
    os.system('git config user.email "romanvm@yandex.ua"')
    open('.nojekyll', 'w').close()
    os.system('git add --all .')
    os.system('git commit -m "Updates {addon} docs to v.{version}"'.format(addon=addon,
                                                                           version=version))
    os.system('git push -f -q "{gh_repo_url}" HEAD:gh-pages'.format(gh_repo_url=gh_repo_url))
    print('{addon} docs v.{version} published to GitHub Pages.'.format(addon=addon,
                                                                       version=version))
