; MsgBox This is ok.  ; 可以用其当做调试语句

; ------------------------重新设置窗口位置大小
Resize(x, y, w, h)                        
{
    WinRestore A                    ;如果当前窗口为最大化或者最小化状态，直接使用WinMove函数是不能移动和改变其大小的
                                    ;所以先使用WinRestore取消其最大化或者最小化状态，A表示当前窗口
    WinMove, A,,x,y, w, h ;调用WinMove函数，按照设定值改变窗口位置和大小
}

; Ctrl+Alt+1重新设置窗口位置大小
^!Numpad1:: Resize(430, 180, 1700, 1050)

GetFilename(txt)
{
	SplitPath, txt, o
	return o
}

; ------------------------打开指定应用
RAMP(ExePath) {    
	tExe:=GetFilename(ExePath)
	if (SubStr(tExe,-3)!=".exe")
        tExe.=".exe"
	if WinExist("ahk_exe" . tExe)
	{
		If WinActive("ahk_exe" . tExe) ; "ahk_exe" 后不需要空格.
		{
			WinMinimize
		}
		else
		{
			WinActivate
		}
	}else{
		Run *RunAs "%ExePath%"
	}
	return
}

OpenBaiduTranslate()
{
    RAMP("D:\Tool\BaiduTranslate\baidu-translate-client\百度翻译.exe")
}

; Ctrl+Up打开百度翻译
; ^Up:: OpenBaiduTranslate()

; ------------------------复制文本并发送快捷键
CopyAndSendKey()
{
    Send ^{c}
    ClipWait, 2
	ifWinExist 沙拉查词-独立查词窗口 ahk_class Chrome_WidgetWin_1
	{
		WinActivate
		Send ^{r}  ; 直接刷新沙拉查词
	}
	else
	{
		Send !{f}  ; 在chrom中为沙拉查词扩展设置的快捷键为Alt+F
	}
	
}
; Ctrl+Space复制当前光标选择文字，并发送快捷键打开chrom插件沙拉查词
F4:: CopyAndSendKey()

; ------------------------在资源管理界面打开Everything并搜索

FindWithEverything()
{
    WinGetClass,o,a

    

    if (o="Progman")
        FilePath=%A_Desktop%
    if(o="CabinetWClass")
    {
        ControlGetText, FilePath, ToolbarWindow323, A 


        ;MsgBox, %FilePath%

        StringReplace, FilePath, FilePath, 地址:%A_space%, , All
  
        if FilePath=桌面
            FilePath=%A_Desktop%
        if FilePath=库\文档
            FilePath=%A_MyDocuments%
        if FilePath in 网上邻居,控制面板,回收站,计算机, 控制面板\所有控制面板项
            FilePath=d:\
    }

    run "D:\Tool\Everything\Everything.exe" -search "%FilePath%%A_space%"
}

; Ctrl+F在资源管理界面打开Everything并搜索
#IfWinActive ahk_class CabinetWClass  ; CabinetWClass是资源管理界面
^f:: FindWithEverything()
#IfWinActive ahk_class Progman  ; Progman是桌面
^f:: FindWithEverything()
#IfWinActive

CloseShaLaWindow()
{
	WinClose 沙拉查词-独立查词窗口 ahk_class Chrome_WidgetWin_1
}

#IfWinActive 沙拉查词-独立查词窗口 ahk_class Chrome_WidgetWin_1
esc:: CloseShaLaWindow()
#IfWinActive



