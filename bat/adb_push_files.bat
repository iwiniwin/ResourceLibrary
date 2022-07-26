set /p src=please input src path:

if "%src:~-20%" == "cdnconfig_debug.json" (
    set dest="sdcard/Android/data/com.garena.game.alphaace/files/OuterPackage/cdnconfig_debug.json"
) else if "%src:~-22%" == "HotfixLocalConfig.json" (
    set dest="sdcard/Android/data/com.garena.game.alphaace/files/OuterPackage/BuildinSetting/HotfixLocalConfig.json"
) else (
    echo reference list:    
    echo    sdcard/Android/data/com.garena.game.alphaace/files
    echo    sdcard/Android/data/com.garena.game.alphaace/files/OuterPackage/BuildinSetting
    set /p dest=please input dest path:
)

adb push  %src% %dest%
pause
