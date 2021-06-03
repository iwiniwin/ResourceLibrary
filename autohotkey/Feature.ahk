GroupAdd, WinGroup, ahk_class Progman ;win7桌面
GroupAdd, WinGroup, ahk_class WorkerW

GroupAdd, WinGroup, ahk_class CabinetWClass ;win7资管
GroupAdd, WinGroup, ahk_class ExploreWClass

Resize(x, y, w, h)                        
{
    WinRestore A                    ;如果当前窗口为最大化或者最小化状态，直接使用WinMove函数是不能移动和改变其大小的
                                    ;所以先使用WinRestore取消其最大化或者最小化状态，A表示当前窗口
    WinMove, A,,x,y, w, h ;调用WinMove函数，按照设定值改变窗口位置和大小
}

ResizeByRatio(x_ratio, y_ratio)
{
    CoordMode, Mouse, Screen
    MouseGetPos, xpos, ypos
    
    SysGet, Mon1, Monitor, 1
    SysGet, Mon2, Monitor, 2
    left:=Mon1Left
    right:=Mon1Right
    top:=Mon1Top
    bottom:=Mon1Bottom
    ;判断鼠标在哪个屏幕上
    if(xpos > Mon1Right) {
        left:=Mon2Left
        right:=Mon2Right
        top:=Mon2Top
        bottom:=Mon2Bottom
    }
    ;MsgBox, Left: %left% -- Top: %top% -- Right: %right% -- Bottom %bottom%.

    width:=right-left
    height:=bottom-top

    w:=width/x_ratio
    h:=height/y_ratio
    x:=(width-w)/2+left
    y:=(height-h)/2+top
    Resize(x, y, w, h)
}

GetFilename(txt)
{
	SplitPath, txt, o
	return o
}

;RunOrActivateOrMinimizeProgram
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

    run "C:\Users\user\Downloads\Everything-1.4.1.1005.x64\Everything.exe" -search "%FilePath%%A_space%"
}

Test()
{
    RAMP("D:\APP\BaiduTranslate\baidu-translate-client\百度翻译.exe")
}

^!Numpad1:: ResizeByRatio(1.45, 1.3)

^Up:: Test()

#IfWinActive ahk_group WinGroup
^f:: FindWithEverything()


