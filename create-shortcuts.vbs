Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Get desktop path
DesktopPath = WshShell.SpecialFolders("Desktop")

' Get current directory
CurrentDir = FSO.GetParentFolderName(WScript.ScriptFullName)

' Create Start Assistant shortcut
Set StartLink = WshShell.CreateShortcut(DesktopPath & "\Start AI Assistant.lnk")
StartLink.TargetPath = CurrentDir & "\start-assistant.bat"
StartLink.WorkingDirectory = CurrentDir
StartLink.IconLocation = "C:\Windows\System32\shell32.dll,14"
StartLink.Description = "Start AI Assistant"
StartLink.Save

' Create Restart Assistant shortcut
Set RestartLink = WshShell.CreateShortcut(DesktopPath & "\Restart AI Assistant.lnk")
RestartLink.TargetPath = CurrentDir & "\restart-assistant.bat"
RestartLink.WorkingDirectory = CurrentDir
RestartLink.IconLocation = "C:\Windows\System32\shell32.dll,238"
RestartLink.Description = "Emergency restart AI Assistant"
RestartLink.Save

' Create Test Assistant shortcut
Set TestLink = WshShell.CreateShortcut(DesktopPath & "\Test AI Assistant.lnk")
TestLink.TargetPath = CurrentDir & "\quick-test.bat"
TestLink.WorkingDirectory = CurrentDir
TestLink.IconLocation = "C:\Windows\System32\shell32.dll,165"
TestLink.Description = "Test AI Assistant system"
TestLink.Save

MsgBox "Desktop shortcuts created successfully!" & vbCrLf & vbCrLf & _
       "- Start AI Assistant" & vbCrLf & _
       "- Restart AI Assistant" & vbCrLf & _
       "- Test AI Assistant", vbInformation, "Shortcuts Created"
