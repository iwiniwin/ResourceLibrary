set /p aab_path=please input aab path:
bundletool build-apks --connected-device --bundle=%aab_path% --output=artifacts/my_app.apks
bundletool install-apks --apks=artifacts/my_app.apks
pause