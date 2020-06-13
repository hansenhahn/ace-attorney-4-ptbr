@echo off

cd Programas
call pack_mes.bat
cd .. 

cd ROM Modificada
call empacotar_rom.bat
call do_patch.bat
cd.. 

