Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
command = """" & shell.ExpandEnvironmentStrings("%ComSpec%") & """ /c cd /d """ & folder & """ && python ""auto_pause_helper.py"" > ""helper.log"" 2>&1"
shell.Run command, 0, False
