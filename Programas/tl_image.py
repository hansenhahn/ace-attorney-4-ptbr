#!/usr/bin/env python
# -*- coding: windows-1252 -*-
'''
Created on 13/06/2020

@author: diego.hahn
'''

import os
import sys
import struct
import math
import array
import glob

from rhImages import images

import argparse

__title__ = "Ace Attorney's Image Unpacker"
__version__ = "1.0"

def gba2tuple(fd):
    rgb = struct.unpack('<H', fd.read(2))[0] & 0x7FFF
    rgb = map(lambda x,y: float((x >> y) & 0x1F)/31.0, [rgb]*3, [0,5,10])
    return rgb
    
def tuple2gba(r, g, b):
	rgb = ((int(b * 31) << 10) | (int(g * 31) << 5) | int(r * 31) ) & 0x7FFF
	return struct.pack('<H', rgb)

def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files
    
def UnpackSprites( src, dst ):
    pass

def UnpackBackground( src, dst ):
    
    print ">> ", src
    
    if not os.path.isdir(dst):
        os.makedirs(dst)
        
    files = filter(lambda x: x.__contains__('.bin'), scandirs(src))
    
    for f in files:
        print ">>  ", f
        with open( f, "rb" ) as ifd:
            if os.path.getsize(f) == 0:
                continue
            
            w, h = struct.unpack("<HH", ifd.read(4))
            flags = h & 0x8000
            h     = h & 0x7fff
            if flags :    # Bitdepth 4
                colormap = [gba2tuple(ifd) for _ in range(16)]
                buffer = ifd.read(w*h/2)
                output = open(os.path.join(dst, os.path.basename(f) + '.bmp'), 'wb')
                w = images.Writer((w, h), colormap, 4, 1, 0)
                w.write(output, buffer, 4, 'BMP')
                output.close()                     
            else:          # Bitdepth 8
                colormap = [gba2tuple(ifd) for _ in range(256)]
                buffer = ifd.read(w*h)
                output = open(os.path.join(dst, os.path.basename(f) + '.bmp'), 'wb')
                w = images.Writer((w, h), colormap, 8, 1, 0)
                w.write(output, buffer, 8, 'BMP')
                output.close()

def PackBackground( src, dst ):
    
    print ">> ", src
                
    files = filter(lambda x: x.__contains__('.bmp'), scandirs(src))

    for _, fname in enumerate(files):
        try:
            print fname 
            basename = fname[len(src)+1:].replace(".bmp", "")
            
            w = images.Reader(fname)
            data, colormap = w.as_data(mode = 1)
            
            with open( os.path.join( dst, basename.replace(".bmp", "") ) , "r+b" ) as ofd:
                if w.bitdepth == 4:
                    ofd.write(struct.pack("<H" , w.width))
                    ofd.write(struct.pack("<H" , w.height & 0x8000))
                elif w.bitdepth == 8:
                    ofd.write(struct.pack("<H" , w.width))
                    ofd.write(struct.pack("<H" , w.height))
                for color in colormap:
                    ofd.write(tuple2gba(*color))
                ofd.write(data)
            
        except:
           print "error!"
        
if __name__ == "__main__":
    import argparse
    
    os.chdir( sys.path[0] )
    os.system( 'cls' )

    print "{0:{fill}{align}70}".format( " {0} {1} ".format( __title__, __version__ ) , align = "^" , fill = "=" )

    parser = argparse.ArgumentParser()
    parser.add_argument( '-m', dest = "mode", type = str, required = True )
    parser.add_argument( '-s', dest = "src", type = str, nargs = "?", required = True )
    parser.add_argument( '-d', dest = "dst", type = str, nargs = "?", required = True )
    
    args = parser.parse_args()    
    
    # src = "..\mes_all.bin"
    # dst = "..\mes_all"
    # Extract(src,dst)    
    # dump text
    if args.mode == "ubg":
        print "Unpacking backgrounds"
        UnpackBackground( args.src , args.dst )
        #UnpackSprites( args.src , args.dst )
    # insert text
    elif args.mode == "pbg": 
        print "Packing backgrounds"
        PackBackground( args.src , args.dst )
    else:
        sys.exit(1)