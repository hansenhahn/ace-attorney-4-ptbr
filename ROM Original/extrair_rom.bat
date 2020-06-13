@echo off

md AA4
cd AA4
..\ndstool -x "..\2036 Apollo Justice - Ace Attorney (US).nds" -9 arm9.bin -7 arm7.bin -y9 y9.bin -y7 y7.bin -d data -y overlay -t banner.bin -h header.bin

