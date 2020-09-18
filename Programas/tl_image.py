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

# Usado para extrair algumas imagens
ARM9_FILE = "arm9.bin"

SHAPE_SIZE = [[( 8, 8),(16,16),(32,32),(64,64)],  # 0
              [(16, 8),(32, 8),(32,16),(64,32)],  # 1
              [( 8,16),( 8,32),(16,32),(32,64)]]  # 2

def gba2tuple(fd):
    c = fd.read(2)
    if not c: c = "\x00\x00"
    rgb = struct.unpack('<H', c)[0] & 0x7FFF
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
    
def UnpackUISprites( src, dst, pal ):
    print ">> ", src
    
    if not os.path.isdir(dst):
        os.makedirs(dst)
        
    files = filter(lambda x: x.__contains__('.bin'), scandirs(src))
    
    with open( pal, "rb" ) as ifd:
        entries = os.path.getsize(pal) / 32
        colormap = [[gba2tuple(ifd) for _ in range(16)] for _ in range(entries)]
    
    with open(ARM9_FILE, "rb") as arm9:
    
        arm9.seek( 0xdfb14 )
        
        for _ in range(89):
            data = arm9.read(0x1c)
            link_data = arm9.tell()
            print "idx:"+str(ord(data[0]))+" desc:"+str(ord(data[1]))+" file:"+str(ord(data[4])),
            arm9.seek(0xd09a8 + 6*ord(data[1]))
            params = struct.unpack("<HHH", arm9.read(6))
            print "columns:"+str((params[0]))+" lines:"+str((params[1]))+" shape:"+str((params[2])),
            arm9.seek(0xd0918 + 4*params[2])
            attr = struct.unpack("<HH", arm9.read(4))
            print "attr0:"+str(hex(attr[0]))+" attr1:"+str(hex(attr[1]))
            arm9.seek(link_data)
            
            fname = os.path.join(src, "%04d.bin" % ord(data[4]))
            
            tile_size = SHAPE_SIZE[attr[0]>>14][attr[1]>>14]
            buffer = ["" for _ in range(params[1]*tile_size[1])]
            print tile_size
            
            with open(fname, "rb") as fd:
                for h0 in range( params[1] ):
                    for w0 in range( params[0] ):
                        for h in range( tile_size[1]/8 ): # 32/8 = 4
                            for w in range( tile_size[0]/8 ): #16 / 8 = 2
                                for dh in range(8):
                                    buffer[tile_size[1]*h0+8*h+dh] += fd.read(4)
                                
                raw_image = ""
                for row in buffer: raw_image += row
                output = open(os.path.join(dst, os.path.basename(fname) + '.bmp'), 'wb')
                w = images.Writer((params[0]*tile_size[0], params[1]*tile_size[1]), colormap[0], 4, 2, 0)
                w.write(output, raw_image, 4, 'BMP')
                output.close()
    
    
    
    

def UnpackBackground( src, dst, pal ):
    
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
                
def UnpackTextures( src, dst ):
    
    print ">> ", src
    
    if not os.path.isdir(dst):
        os.makedirs(dst)
        
    files = filter(lambda x: x.__contains__('.bin'), scandirs(src))
    
    for f in files:
        print ">>  ", f
        try:
            with open( f, "rb" ) as ifd:
                if os.path.getsize(f) == 0:
                    continue
                
                b, w, h, _ = struct.unpack("BBBB", ifd.read(4))
                w = 8 << w
                h = 8 << h
                img_addr, img_size = struct.unpack("<LL", ifd.read(8)) 
                pal_addr, pal_size = struct.unpack("<LL", ifd.read(8)) 
                
                ifd.seek(img_addr)
                buffer = ifd.read(img_size)
                
                ifd.seek(pal_addr)            
     
                output = open(os.path.join(dst, os.path.basename(f) + '.bmp'), 'wb') 
                if b == 1:
                    colormap = [gba2tuple(ifd) for _ in range(256)]
                    for i,x in enumerate(buffer):
                        buffer[i] == chr(ord(x) & 0x1F)
                    w = images.Writer((w, h), colormap, 8, 2, 0)
                    w.write(output, buffer, 8, 'BMP')
                elif b == 3 :    # Bitdepth 4
                    colormap = [gba2tuple(ifd) for _ in range(16)]
                    w = images.Writer((w, h), colormap, 4, 2, 0)
                    w.write(output, buffer, 4, 'BMP')                  
                elif b == 4:          # Bitdepth 8
                    colormap = [gba2tuple(ifd) for _ in range(256)]
                    w = images.Writer((w, h), colormap, 8, 2, 0)
                    w.write(output, buffer, 8, 'BMP')
                elif b == 6:
                    colormap = [gba2tuple(ifd) for _ in range(256)]
                    for i,x in enumerate(buffer):
                        buffer[i] == chr(ord(x) & 0x7)
                    w = images.Writer((w, h), colormap, 8, 2, 0)
                    w.write(output, buffer, 8, 'BMP')
                else:
                    print "error"
                output.close()   
        except:
            print "error"
            
def PackTextures( src, dst ):
    print ">> ", src
                
    files = filter(lambda x: x.__contains__('.bmp'), scandirs(src))

    for _, fname in enumerate(files):
        try:
            print fname 
            basename = fname[len(src)+1:].replace(".bmp", "")
            
            w = images.Reader(fname)
            data, colormap = w.as_data(mode = 2)
            
            with open( os.path.join( dst, basename.replace(".bmp", "") ) , "r+b" ) as ofd:
                if w.bitdepth == 4:
                    ofd.write(struct.pack("B",3))
                elif w.bitdepth == 8:
                    ofd.write(struct.pack("B",4))
                    
                ofd.write(struct.pack("B" , int(math.log(w.width/8,2))))
                ofd.write(struct.pack("B" , int(math.log(w.height/8,2))))
                ofd.write(struct.pack("B" , 0))
                
                ofd.write(struct.pack("<L" , 0x14))
                ofd.write(struct.pack("<L" , len(data)))
                ofd.write(struct.pack("<L" , 0x14 + len(data)))
                ofd.write(struct.pack("<L" , 2*len(colormap)))                         
                  
                ofd.write(data)
                for color in colormap:
                    ofd.write(tuple2gba(*color))
                ofd.write(data)
            
        except:
           print "error!"    

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
    parser.add_argument( '-p', dest = "pal", type = str, nargs = "?", required = False )
    
    args = parser.parse_args()    
    
    # src = "..\mes_all.bin"
    # dst = "..\mes_all"
    # Extract(src,dst)    
    # dump text
    if args.mode == "ubg":
        print "Unpacking backgrounds"
        UnpackBackground( args.src , args.dst )
    elif args.mode == "uui":
        print "Unpacking UI sprites"
        UnpackUISprites( args.src , args.dst , args.pal )
    elif args.mode == "utex":
        print "Unpacking textures"
        UnpackTextures( args.src, args.dst )
    elif args.mode == "ptex": 
        print "Packing textures"
        PackTextures( args.src , args.dst )
    # insert text
    elif args.mode == "pbg": 
        print "Packing backgrounds"
        PackBackground( args.src , args.dst )
    else:
        sys.exit(1)