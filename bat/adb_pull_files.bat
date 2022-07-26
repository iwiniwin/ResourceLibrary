set files_path="E:\PerfectWorld\Commands\artifacts\device_Files"
if exist %files_path% rd /s /q %files_path%
adb pull sdcard/Android/data/com.garena.game.alphaace/files %files_path%
if exist %files_path% (
    start explorer %files_path%
    exit
)
echo "pull files failed"
pause

