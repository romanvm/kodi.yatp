#-*- coding: utf-8 -*-
'''
    Torrenter v2 plugin for XBMC/Kodi
    Copyright (C) 2015 srg70, RussakHH, DiMartino
'''

import os

from platform_pulsar import get_libname

class Public:
    def __init__( self ):
        self.platforms=[]
        self.root=os.path.dirname(__file__)
        for dir in os.listdir(self.root):
            if os.path.isdir(os.path.join(self.root,dir)):
                for subdir in os.listdir(os.path.join(self.root,dir)):
                    if os.path.isdir(os.path.join(self.root,dir,subdir)):
                        self.platforms.append({'system':dir, 'version':subdir})
        self._generate_size_file()

    def _generate_size_file( self ):
        for platform in self.platforms:
            for libname in get_libname(platform):
                self.libname=libname
                self.platform=platform
                self.libdir = os.path.join(self.root, self.platform['system'], self.platform['version'])
                self.libpath = os.path.join(self.libdir, self.libname)
                self.sizepath=self.libpath+'.size.txt'
                self.zipname=self.libname+'.zip'
                zippath=os.path.join(self.libdir, self.zipname)
                system=platform['system']+'/'+platform['version']+'/'
                if os.path.exists(self.libpath):
                    if not os.path.exists(self.sizepath):
                        print system+self.libname+' NO SIZE'
                        self._makezip()
                    elif not os.path.exists(zippath):
                        print system+self.libname+' NO ZIP'
                        self._makezip()
                    else:
                        size=str(os.path.getsize(self.libpath))
                        size_old=open( self.sizepath, "r" ).read()
                        if size_old!=size:
                            print system+self.libname+' NOT EQUAL'
                            self._makezip()
                        else:
                            print system+self.libname+' NO ACTION'
                else:
                    print system+self.libname+' NO LIB'

    def _makezip(self):
        open( self.sizepath, "w" ).write( str(os.path.getsize(self.libpath)) )
        os.chdir(self.libdir)
        os.system('del %s' % (self.zipname))
        os.system('"C:\\Program Files\\7-Zip\\7z.exe" a %s.zip %s' %
                  (self.libname, self.libname))
        os.chdir(self.root)
        #os.system('"C:\\Program Files\\7-Zip\\7z.exe" a %s.zip %s' %
        #          (self.platform['system']+os.sep+self.libname, self.platform['system']+os.sep+self.libname))

if ( __name__ == "__main__" ):
    # start
    #TODO: publicate
    Public()