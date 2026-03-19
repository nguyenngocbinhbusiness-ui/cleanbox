!ifndef SRC_DIR
  !define SRC_DIR "dist\CleanBox.dist"
!endif

!include "MUI2.nsh"

Name "CleanBox"
OutFile "dist\CleanBox_Setup.exe"
InstallDir "$LOCALAPPDATA\CleanBox"
InstallDirRegKey HKCU "Software\CleanBox" ""
RequestExecutionLevel user

!define MUI_ABORTWARNING
!define MUI_ICON "src\assets\icon.ico"
!define MUI_UNICON "src\assets\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy the application files
    File /r "${SRC_DIR}\*"
    
    ; Create shortcuts
    CreateShortcut "$DESKTOP\CleanBox.lnk" "$INSTDIR\CleanBox.exe"
    CreateDirectory "$SMPROGRAMS\CleanBox"
    CreateShortcut "$SMPROGRAMS\CleanBox\CleanBox.lnk" "$INSTDIR\CleanBox.exe"
    CreateShortcut "$SMPROGRAMS\CleanBox\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Write registry keys
    WriteRegStr HKCU "Software\CleanBox" "" $INSTDIR
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CleanBox" "DisplayName" "CleanBox"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CleanBox" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CleanBox" "DisplayIcon" "$INSTDIR\CleanBox.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\CleanBox.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$DESKTOP\CleanBox.lnk"
    Delete "$SMPROGRAMS\CleanBox\CleanBox.lnk"
    Delete "$SMPROGRAMS\CleanBox\Uninstall.lnk"
    RMDir "$SMPROGRAMS\CleanBox"
    
    DeleteRegKey HKCU "Software\CleanBox"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\CleanBox"
SectionEnd
