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

__title__ = "Ace Attorney's Text Processor"
__version__ = "1.0"

# O Arquivo de saída deve ser o mais próximo possível ao gerado pela ferramenta do onepiecefreak

# Valor binário : (Nome amigável, Argumentos)
tagsdict = { 0x00 : ("bop",0), 0x01 : ("b",0), 0x02 : ("p",0), 0x03 : ("color",1),
            0x04 : ("pause",0), 0x05 : ("music",2), 0x06 : ("sound",2), 0x07 : ("fullscreen_text",0),
            0x08 : ("2args_choice_jmp",2), 0x09 : ("3args_choice_jmp",3), 0x0a : ("rejmp",1), 0x0b : ("speed",1),
            0x0c : ("wait",1), 0x0d : ("endjmp",0), 0x0e : ("name",1), 0x0f : ("testimony_box",2),
            0x10 : ("0x10",1), 0x11 : ("evd_window_plain",0), 0x12 : ("bgcolor",3), 0x13 : ("showphoto",1),
            0x14 : ("removephoto",0), 0x15 : ("special_jmp",0), 0x16 : ("savegame",0), 0x17 : ("newevidence",1),
            0x18 : ("0x18",1), 0x19 : ("0x19",2), 0x1a : ("swoosh",4), 0x1b : ("bg",1),
            0x1c : ("hidetextbox",1), 0x1d : ("0x1d",1), 0x1e : ("person",3), 0x1f : ("hideperson",0),
            0x20 : ("0x20",1), 0x21 : ("evidence_window_lifebar",0), 0x22 : ("fademusic",1), 0x23 : ("0x23",1),
            0x24 : ("reset",0), 0x25 : ("0x25",1), 0x26 : ("0x26",1), 0x27 : ("shake",2),
            0x28 : ("testimony_animation",1), 0x29 : ("0x29",1), 0x2a : ("0x2a",3), 0x2b : ("0x2b",0),
            0x2c : ("jmp",1), 0x2d : ("nextpage_button",0), 0x2e : ("nextpage_nobutton",0), 0x2f : ("animation",2),
            0x30 : ("0x30",1), 0x31 : ("personvanish",2), 0x32 : ("0x32",2), 0x33 : ("0x33",5),
            0x34 : ("fadetoblack",1), 0x35 : ("0x35",2), 0x36 : ("raw_jmp",1), 0x37 : ("0x37",2),
            0x38 : ("0x38",1), 0x39 : ("littlesprite",1), 0x3a : ("0x3a",3), 0x3b : ("0x3b",2),
            0x3c : ("0x3c",1), 0x3d : ("0x3d",1), 0x3e : ("0x3e",1), 0x3f : ("0x3f",0),
            0x40 : ("0x40",0), 0x41 : ("0x41",0), 0x42 : ("soundtoggle",1), 0x43 : ("lifebar",1),
            0x44 : ("guilty",1), 0x45 : ("0x45",0), 0x46 : ("bgtile",1), 0x47 : ("0x47",2),
            0x48 : ("0x48",2), 0x49 : ("wingame",0), 0x4a : ("0x4a",0), 0x4b : ("0x4b",1),
            0x4c : ("0x4c",0), 0x4d : ("0x4d",2), 0x4e : ("wait_noanim",1), 0x4f : ("0x4f",7),
            0x50 : ("0x50",1), 0x51 : ("0x51",2), 0x52 : ("0x52",0), 0x53 : ("0x53",0),
            0x54 : ("lifebarset",2), 0x55 : ("0x55",2), 0x56 : ("0x56",2), 0x57 : ("psychelock",1),
            0x58 : ("0x58",0), 0x59 : ("0x59",0), 0x5a : ("0x5a",0), 0x5b : ("0x5b",2),
            0x5c : ("0x5c",0), 0x5d : ("center_text",1), 0x5e : ("0x5e",0), 0x5f : ("0x5f",3), 0x60 : ("0x60",5),
            0x61 : ("0x61",5), 0x62 : ("0x62",2), 0x63 : ("0x63",0), 0x64 : ("0x64",0),
            0x65 : ("0x65",2), 0x66 : ("0x66",3), 0x67 : ("0x67",0), 0x68 : ("0x68",0),
            0x69 : ("bganim",2), 0x6a : ("switchscript",1), 0x6b : ("0x6b",3), 0x6c : ("0x6c",1),
            0x6d : ("0x6d",1), 0x6e : ("0x6e",1), 0x6f : ("0x6f",1), 0x70 : ("0x70",2),
            0x71 : ("0x71",3), 0x72 : ("0x72",0), 0x73 : ("0x73",0), 0x74 : ("0x74",2),
            0x75 : ("0x75",0), 0x76 : ("0x76",2), 0x77 : ("0x77",1), 0x78 : ("0x78",1),
            0x79 : ("0x79",0), 0x7a : ("0x7a",1), 0x7b : ("0x7b",0), 0x7c : ("0x7c",1),
            0x7d : ("0x7d",0), 0x7e : ("0x7e",0), 0x7f : ("0x7f",1),
            0x80 : ("0x80",0), 0x81 : ("0x81",0), 0x82 : ("0x82",0), 0x83 : ("0x83",0), 0x84 : ("0x84",0), 0x85 : ("0x85",0), 
            0x86 : ("0x86",0), 0x87 : ("0x87",0), 0x88 : ("0x88",0), 0x89 : ("0x89",0), 0x8a : ("0x8a",0), 0x8b : ("0x8b",0),
            0x8c : ("0x8c",0), 0x8d : ("0x8d",0), 0x8e : ("0x8e",2), 0x8f : ("0x8f",1) }

NEW_BLOCK_TAG = r'^({{.+?}})$'
TAG_IN_LINE = r'({.+?})'
GET_TAG = r'^{(.+?)}$'

def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files            
            
def Insert(src,dst):
    table = normal_table('phoenix.tbl')
    table.fill_with('00B4=a', '009A=A', '0090=0') 
    table.add_items('018F= ')
    table.set_mode('inverted')
    
    txt_path = os.path.join(src, 'mes_text')
    files = filter(lambda x: x.__contains__('.txt'), scandirs(txt_path))   

    # Cria o dicionário invertido de tags
    itagsdict = dict([[v[0],k] for k,v in tagsdict.items()])
    for kk, txtname in enumerate(files):
        print ">> Convertendo e comprimindo " + txtname

        text_blocks = []
        do_not_delete_blocks = []
        with open(txtname, 'rb') as fd:
            buffer = None
            xx = 0
            
            tag35_address = 0
            tag35_ptr_table1 = []
            tag35_ptr_table2 = [] 
            do_not_delete_count = 0
            do_not_delete_table = []
            
            for line in fd:
                xx += 1
                try:
                    line = line.strip('\r\n')
                    if not line:
                        continue
                    elif re.match( NEW_BLOCK_TAG, line ):
                        if buffer:
                            tag35_address += len(buffer)
                            text_blocks.append(buffer)
                        buffer = array.array("c")
                    elif "do_not_delete" in line:
                        splitted = re.split( TAG_IN_LINE, line )
                        for string in splitted:
                            tag = re.match( GET_TAG, string )
                            if not tag:
                                continue
                            else:
                                tag = tag.groups()[0]
                                argv = []
                                if ": " in tag:
                                    tag,argv = tag.split(": ")
                                    argv = argv.split(" ")                                
                                if "do_not_delete" in tag:
                                    # Atualizar a tag conforme as referências
                                    if len(do_not_delete_table) > 0:
                                        for data in do_not_delete_table:
                                            if data[0] == (len(text_blocks) + do_not_delete_count):                                      
                                                do_not_delete_blocks.append(((data[1]<<16)|data[2]) & 0xFFFFFFFF) 
                                    # Caso o contrário, atualiza
                                    else:
                                        for arg in argv:
                                            do_not_delete_blocks.append(int(arg)) 
                                    do_not_delete_count += 1
                    else:
                        splitted = re.split( TAG_IN_LINE, line )
                        for string in splitted:
                            tag = re.match( GET_TAG, string )
                            # Se não for uma tag, é texto plano
                            if not tag:                            
                                for char in string:
                                    try:
                                        buffer.extend( table[char][::-1] )
                                    except:
                                        print xx, ord(char)
                                        raise Exception()
                            # Se for uma tag
                            else:
                                tag = tag.groups()[0]
                                argv = []
                                # Tag com argumentos
                                if ": " in tag:
                                    tag,argv = tag.split(": ")
                                    argv = argv.split(" ")
                                    
                                if tag.startswith("@"): # São labels
                                    if "RelativeAddress" in tag:
                                        # Ponteiro relativo ao inicio do bloco    
                                        tag35_ptr_table2.append( [tag, len(buffer)] )
                                    elif "DoNotDelete" in tag:
                                        bindex = int(tag[len("@DoNotDelete"):])
                                        do_not_delete_table.append( [ bindex, len(text_blocks), len(buffer) ])                                        
                                else:                                                                    
                                    # A tag 35h é especial.
                                    if tag == "0x35":
                                        buffer.extend( struct.pack("<H", itagsdict[tag]) )
                                        buffer.extend( struct.pack("<H", int(argv[0])) )
                                        if argv[1].startswith("@"):
                                            # Bufferiza as tags 0x35 que vão precisar serem atualizadas
                                            tag35_ptr_table1.append( [argv[1], tag35_address + len(buffer)] )                                   
                                            buffer.extend( struct.pack("<H", 0) )
                                        else:
                                            buffer.extend( struct.pack("<H", int(argv[1])) )
                                    else:
                                        if tag in itagsdict:
                                            buffer.extend( struct.pack("<H", itagsdict[tag]) )
                                            for arg in argv:
                                                buffer.extend( struct.pack("<H", int(arg)) )                            
                                        else:
                                            buffer.extend( struct.pack("<H", int(tag)) )
                                        
                except:
                    print xx, line
                    sys.exit()
                                
            if len(buffer) > 0 and len(do_not_delete_blocks) == 0:
                text_blocks.append(buffer)                                                                    

            # É necessário saber o tamanho para alocar o mmap
            entries = len(text_blocks) + len(do_not_delete_blocks)
            text_address = 4 + 4*entries
            size = text_address + sum(map(lambda x: len(x), text_blocks))            
            temp = mmap.mmap(-1,size)
            temp.seek(text_address)
            
            ptr_table = []
            total = 0 
            for j, text in enumerate(text_blocks):
                ptr_table.append( temp.tell() )
                temp.write( text )
                
            for data in do_not_delete_blocks:
                ptr_table.append(data)
            
            temp.seek(0)
            temp.write( struct.pack("<L", entries) )
            for ptr in ptr_table:
                temp.write( struct.pack("<L", ptr) )
            
            # Atualiza tag 35h:
            for tag in tag35_ptr_table1:
                #print tag
                temp.seek(text_address + tag[1])
                for ret in tag35_ptr_table2:
                    #print ret
                    if tag[0] == ret[0]:
                        temp.write( struct.pack("<H", ret[1]) )
                        #raw_input()
                        break
                     

            ret = lzss.compress(temp)
            filepath = os.path.join(src,"%03d.bin" % (kk))
            path  = os.path.dirname( filepath )
            if not os.path.isdir( path ):
                os.makedirs( path )

            with open(filepath, 'wb') as fd:
                ret.tofile(fd)
                            
            # # DEBUG . Desnecessário
            filepath = "../mes_all_novo/mes_temp/" + "%03d.bin" % (kk)
            path  = os.path.dirname( filepath )
            if not os.path.isdir( path ):
                os.makedirs( path )    
            
            with open(filepath, 'wb') as fd:                        
                temp.seek(0)
                fd.write(temp.read())
                
                # ptr_table = []
                # for text in text_blocks:
                    # ptr_table.append( fd.tell() )
                    # fd.write( text )
                    
                # for data in do_not_delete_blocks:
                    # ptr_table.append(data)
                
                # fd.seek(0)
                # fd.write( struct.pack("<L", entries) )
                # for ptr in ptr_table:
                    # fd.write( struct.pack("<L", ptr) )  

                # for tag in tag35_ptr_table1:
                    # fd.seek(text_address + tag[1])
                    # for ret in tag35_ptr_table2:
                        # if tag[0] == ret[0]:
                            # fd.write( struct.pack("<H", ret[1]) )
                            # break
                    

    # Gerar o mes_all.bin finalmente
    files = filter(lambda x: x.__contains__('.bin'), os.listdir( src )) 
    with open(dst, "wb") as fd:
        entries = len(files)
        
        ptr_table = []
        fd.seek(4+8*entries)
        for f in files:                    
            with open(os.path.join(src,f), "rb") as inp:
                ret = inp.read()
                ptr_table.append( [fd.tell(), len(ret)] )
                fd.write(ret)
                while fd.tell() % 4 > 0: fd.write("\x00")
        
        fd.seek(0)
        fd.write( struct.pack("<L", entries) )
        for ptr in ptr_table:
            fd.write( struct.pack("<LL",*ptr) )    

def Extract(src,dst):
    table = normal_table('phoenix.tbl')
    table.fill_with('00B4=a', '009A=A', '0090=0') 
    table.add_items('018F= ')

    assert os.path.isfile(src), "Invalid file"
    
    tmpdst = os.path.join( dst, "mes_temp" )
    txtdst = os.path.join( dst, "mes_text" )
    
    if not os.path.isdir(txtdst):
        os.makedirs(txtdst)
        
    if not os.path.isdir(tmpdst):
        os.makedirs(tmpdst)        
        
    with open(src, "rb") as fd:
        entries = struct.unpack("<L", fd.read(4))[0]
        ptr_table = []
        for _ in range(entries):
            ptr_table.append(struct.unpack("<LL", fd.read(8)))
            
        for i, data in enumerate(ptr_table):
            fd.seek(data[0])
            with open( os.path.join(dst, "%03d.bin" % i), "wb" ) as out:
                out.write( fd.read(data[1]) )

    for k in range(entries):
        filepath = os.path.join(dst, "%03d.bin" % k)
        with open( filepath, "rb" ) as fd:
            ret = lzss.uncompress(fd, 0)
            # Não é um arquivo comprimido em lzss
            if not ret: # or (k % 2 == 0):
                continue
            
            # # Debug, não é necessario
            tmp = open(os.path.join(tmpdst, "%03d.bin" % k), "wb")
            tmp.write(ret)
            tmp.close()
                
            print ">> Descomprimindo e convertendo " + filepath
            # Cria um temporário
            temp = mmap.mmap(-1, len(ret))
            temp.write(ret)
            temp.seek(0)
            
            entries = struct.unpack("<L", temp.read(4))[0]
            ptr_table = []
            size_table = []
            do_not_delete_table = []
            for _ in range(entries):
                ptr = struct.unpack("<L", temp.read(4))[0]
                if ptr >= len(ret):
                    do_not_delete_table.append(ptr)
                else:
                    ptr_table.append(ptr)
            for i in range(len(ptr_table)-1):
                size_table.append( ptr_table[i+1] - ptr_table[i] )
            size_table.append( len(ret) - ptr_table[-1] )
            
            buffer = array.array("c")
            
            tag35 = 0
            tag35_ptr_table = []
            
            do_not_delete_table2 = []
            for i, data in enumerate(do_not_delete_table):
                do_not_delete_table2.append( [len(ptr_table)+i, data >> 16 , data & 0xFFFF] )
            
            # A primeira iteração é para bufferizar as tags 35h
            for i, ptr in enumerate(ptr_table):
                if ptr >= len(ret):
                    continue
                    
                temp.seek(ptr)
                
                while True:
                    b = temp.read(2)
                    c = struct.unpack("<H", b)[0]
                    if c < 0x90: # É uma tag.. esse teste é o mesmo do jogo
                        if c in tagsdict:
                            tag = tagsdict[c][0]
                            if c == 0x35: # Tag 0x35 .. tem um tratamento especial :)
                                arg1 = struct.unpack("<H", temp.read(2))[0]
                                # Só vamos avaliar se o bit 7 for 0
                                if ( arg1 & 0x80 ) == 0:
                                    # Calcula o salto absoluto
                                    tag35_ptr_table.append( ptr + (struct.unpack("<H", temp.read(2))[0] & 0xFFFE) )
                                    tag35 += 1 
                                else: 
                                    temp.read(2)
                            else:
                                for _ in range(tagsdict[c][1]):
                                    temp.read(2)
                        else:
                            raise Exception("Missing %02x tag" % c)

                    if temp.tell() >= (ptr+size_table[i]):
                        break  

            tag35 = 0
            #print tag35_ptr_table
            #print do_not_delete_table2
            for i, ptr in enumerate(ptr_table):
                buffer.extend("\n\n{{%d}}\n" % i)
                if ptr >= len(ret):
                    buffer.write("{bop}{do_not_delete: "+str(ptr)+" }{endjmp}")
                    continue              
                    
                temp.seek(ptr)
                
                breakline = False
                while True:
                    if tag35_ptr_table:
                        addr = temp.tell()
                        for tag35_1, tag35_ptr in enumerate(tag35_ptr_table):
                            if tag35_ptr == addr:
                                buffer.extend("{@RelativeAddress%d}" % tag35_1)

                    if do_not_delete_table2:
                        addr = temp.tell() - ptr # Endereço relativo ao inicio do bloco
                        for donot_ptr in do_not_delete_table2:
                            if donot_ptr[1] == i and donot_ptr[2] == addr:
                                buffer.extend("{@DoNotDelete%d}" % donot_ptr[0])
                
                    b = temp.read(2)
                    c = struct.unpack("<H", b)[0]
                    if c < 0x90: # É uma tag.. esse teste é o mesmo do jogo
                        #breakline = True
                        if c in tagsdict:
                            tag = tagsdict[c][0]
                            content = ""
                            if c == 0x35: # Tag 0x35 .. tem um tratamento especial :)
                                arg1 = struct.unpack("<H", temp.read(2))[0]
                                content += " %d" % arg1
                                # Só vamos olhar as tags 35 que apontam para o começo do bloco (bit7 0)
                                if (arg1 & 0x80) == 0:
                                    arg2 = struct.unpack("<H", temp.read(2))[0]
                                    content += " @RelativeAddress%d" % tag35
                                    tag35 += 1                            
                                else:
                                    arg2 = struct.unpack("<H", temp.read(2))[0]
                                    content += " %d" % arg2                                                         
                            else:
                                for _ in range(tagsdict[c][1]):
                                    content += " %d" % struct.unpack("<H", temp.read(2))[0]
                            if content:
                                buffer.extend( "{"+tag+":"+content+"}" )
                            else:
                                buffer.extend( "{"+tag+"}" )                                
                        else:
                            raise Exception("Missing %02x tag" % c)
                            
                        if c in ( 0x01 , 0x02, 0x2d, 0x2e ): breakline = True   
                    else:
                        if breakline:
                            breakline = False
                            buffer.append("\n") # Eita POG do caralho
                    
                        b = b[::-1]
                        if b in table:
                            buffer.append( table[b] )
                        else:
                            buffer.extend( "{"+str(c)+"}")
                    
                    if temp.tell() >= (ptr+size_table[i]):
                        break
            
            temp.close()
            
            for i, data in enumerate(do_not_delete_table):
                buffer.extend("\n\n{{%d}}\n" % (i+len(ptr_table)))
                buffer.extend("{bop}{do_not_delete: "+str(data)+"}{endjmp}")
            
            txtpath = os.path.join(txtdst, "%03d.txt" % k)            
            out = open(txtpath, "wb" )
            buffer.tofile(out)
            out.close()
            
                
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
    
    
    