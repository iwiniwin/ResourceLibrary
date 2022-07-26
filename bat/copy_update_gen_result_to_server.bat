xcopy /y E:\PerfectWorld\cdn\update\update_gen_result\config\update_tools\*.* E:\PerfectWorld\Server\update\update_tools
del /s /Q E:\PerfectWorld\Server\cdn\update\update_tools
xcopy E:\PerfectWorld\cdn\update\update_gen_result\patch\update_tools\*.* E:\PerfectWorld\Server\cdn\update\update_tools