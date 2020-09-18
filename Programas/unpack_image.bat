@echo off

rem pypy tool_cpac.py -m e -s "..\ROM Original\AA4\data\cpac_2d.bin" -d "..\Arquivos Originais"
rem pypy tl_image.py -m e -s "..\Arquivos Originais\cpac_2d\003" -d "..\Imagens Originais\cpac_2d\003"
rem pypy tl_image.py -m ubg -s "..\Arquivos Originais\cpac_2d\0004" -d "..\Imagens Originais\cpac_2d\0004"

rem pypy tl_image.py -m uui -s "..\Arquivos Originais\cpac_2d\0005" -d "..\Imagens Originais\cpac_2d\0005" -p "..\Arquivos Originais\cpac_2d\0000\0008.bin"

pypy tl_image.py -m utex -s "..\Arquivos Originais\cpac_3d\0000" -d "..\Imagens Originais\cpac_3d\0000"