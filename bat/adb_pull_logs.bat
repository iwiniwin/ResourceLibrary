set logs_path="E:\PerfectWorld\Commands\artifacts\device_Logs"
set decrypt_exe="F:\Garena\trunk\tools\D11Decryptor\D11Decryptor.exe"
if exist %logs_path% rd /s /q %logs_path%
adb pull sdcard/Android/data/com.garena.game.alphaace/files/_Logs %logs_path%
if exist %logs_path% (
    for %%i in (%logs_path%\*E.log) do ( %decrypt_exe% %%i )
    start explorer %logs_path%
    exit
)
echo "pull logs failed"
pause

