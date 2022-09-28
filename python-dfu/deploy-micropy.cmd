
set AMPY_PORT=COM6

for /d /r ".\lib" %%a in (__pycache__\) do if exist "%%a" rmdir /s /q "%%a"
for /d /r ".\app" %%a in (__pycache__\) do if exist "%%a" rmdir /s /q "%%a"
for /d /r ".\src" %%a in (__pycache__\) do if exist "%%a" rmdir /s /q "%%a"

ampy put secrets.json
ampy put lib lib
ampy put app ./
ampy put src ./
