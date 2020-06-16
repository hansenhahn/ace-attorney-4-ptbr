#!/usr/bin/env python
# -*- coding: windows-1252 -*-
'''
Created on 17/02/2018

@author: diego.hahn
'''

import tempfile
import os
import sys
import struct
import array
import shutil
import datetime
import mmap
import re
import glob

from pytable import normal_table
from rhCompression import lzss, rle, huffman

import argparse

__title__ = "Ace Attorney's CPAC Unpacker"
__version__ = "1.0"

def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files            
            
def Insert(src,dst):
    src = os.path.join( src, "cpac_2d")

    folders  = [os.path.join( src , "%04d" % 4 ),]
                
               
    attr = {}
    with open( "do_not_delete_cpac_2d_traduzidos.log", "r" ) as log:
        for l in log.readlines():
            f, flag = l.split(" > ")
            attr.update({f:flag})

    for folder in folders:
        files = filter(lambda x: x.__contains__('.bin'), scandirs(folder))
        entries = len(files)
        print ">> ", folder + ".bin"
        with open( folder + ".bin" , "wb" ) as ofd:
            ofd.write( struct.pack("<L", 0x18) )
            ofd.write( struct.pack("<L", 0x02) )
            ofd.write( "YEKB" )
            ofd.write( struct.pack("<L", 0x18) )
            ofd.write( "TADB" )
            ofs = 4+entries * 8 + ofd.tell()
            ofd.write( struct.pack("<L", ofs) )
            link_tbl = ofd.tell()
            ofd.seek(entries*8, 1)
            link_dat = ofd.tell()
        
            for f in files:
                print " >> Updating ", f
                ifd = open(f, "rb")
                if "-" in attr[f]:
                #if True:
                    data = ifd.read()
                    flag = 0
                else:
                    data = lzss.compress(ifd).tostring()
                    flag = 0x80000000
                ifd.close()
                    
                while len(data) % 4 != 0:
                    data += "\x00"

                ofd.seek(link_tbl)
                ofd.write(struct.pack("<L", link_dat-ofs))
                ofd.write(struct.pack("<L", len(data) | flag))
                link_tbl += 8
                
                ofd.seek(link_dat)
                ofd.write(data)
                link_dat += len(data)
                
    files = filter(lambda x: x.__contains__('.bin'), glob.glob( os.path.join(src, '*')))            
    with open( dst, "wb" ) as ofd:
        link_tbl = ofd.tell()
        ofd.seek( len(files)*8 )
        link_dat = ofd.tell()
        
        for f in files:
            print " >> Updating ", f , ">" , dst , hex(link_dat)
            ifd = open(f, "rb")
            data = ifd.read()
            ifd.close() 

            ofd.seek(link_tbl)
            ofd.write(struct.pack("<L", link_dat))
            ofd.write(struct.pack("<L", len(data)))
            link_tbl += 8 

            ofd.seek(link_dat)            
            ofd.write(data)
            link_dat += len(data)
                
                

def Extract(src,dst):

    assert os.path.isfile(src), "Invalid file"
    
    print ">> ", src
    
    with open( "do_not_delete_cpac_2d.log", "w" ) as log:
        outpath = os.path.join( dst, "cpac_2d" )
        if not os.path.isdir(outpath):
            os.makedirs(outpath)   
        
        with open( src, "rb" ) as ifd:
            entries = struct.unpack("<L", ifd.read(4))[0] / 8
            
            ifd.seek(0)
            ptr_table = []
            for _ in range(entries):
                ptr_table.append( struct.unpack("<2L", ifd.read(8)) )
                
            for i, tpl in enumerate(ptr_table):
                ofs, size = tpl
                ifd.seek(ofs)
                with open( os.path.join( outpath , "%04d.bin" % i ), "wb" ) as ofd:
                    ofd.write(ifd.read(size))
            
        #files = filter(lambda x: x.__contains__('.bin'), scandirs(outpath))   
        files  = [os.path.join( outpath , "%04d.bin" % 1 ),
                    os.path.join( outpath , "%04d.bin" % 2 ),
                    os.path.join( outpath , "%04d.bin" % 3 ),
                    os.path.join( outpath , "%04d.bin" % 4 ),
                    os.path.join( outpath , "%04d.bin" % 5 ),]
        for fname in files:
            try:
                dst_path = fname[:-4]
                if not os.path.isdir(dst_path):
                    os.makedirs(dst_path)    
            
                with open( fname, "rb" ) as ifd:
                    ifd.read(4)          # 0000 0018h
                    ifd.read(4)          # 0000 0002h
                    stamp = ifd.read(4)
                    assert stamp == "YEKB" #or stamp == "YEKP"
                    ifd.read(4)          # 0000 0018h
                    stamp = ifd.read(4)
                    assert stamp == "TADB" #or stamp == "TADP"
                    ofs = struct.unpack("<L", ifd.read(4))[0]
                    entries = (ofs - ifd.tell()) / 8
            
                    ptr_table = []
                    for _ in range(entries):
                        ofs_rel, size =  struct.unpack("<2L", ifd.read(8))
                        flag = size & 0x80000000
                        size = size & 0x7fffffff
                        ptr_table.append( (ofs+ofs_rel, size, flag) )
                        
                    for i, tpl in enumerate(ptr_table):
                        ofs, size, flag = tpl

                        with open( os.path.join( dst_path , "%04d.bin" % i ), "wb" ) as ofd:
                            print ">> Extracting ", os.path.join( dst_path , "%04d.bin" % i )
                        
                            if ( flag ):
                                log.write( "%s > COMPRESSED\n" % os.path.join( dst_path , "%04d.bin" % i ) )
                                ret = lzss.uncompress(ifd, ofs)
                                ret.tofile(ofd)
                            else:
                                log.write( "%s > -\n" % os.path.join( dst_path , "%04d.bin" % i ) )
                                ifd.seek(ofs)
                                ofd.write(ifd.read(size))  
            except AssertionError:
                print "File not supported yet."           
                
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
    if args.mode == "e":
        print "Desempacotando arquivo"
        Extract( args.src , args.dst )
    # insert text
    elif args.mode == "i": 
        print "Criando arquivo"
        Insert( args.src , args.dst )
    else:
        sys.exit(1)
    
    
    