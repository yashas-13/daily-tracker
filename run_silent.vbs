' Silent launcher for Daily Tracker
' Runs the tracker with pythonw.exe (no console window)
' Usage: wscript run_silent.vbs

Option Explicit

Dim fso, shell, scriptDir, pythonwPath, trackerScript, command, wshShell

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Get the directory where this script is located
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Find pythonw.exe - try common locations
Dim pythonwCandidates
pythonwCandidates = Array( _
    scriptDir & "\venv\Scripts\pythonw.exe", _
    "pythonw.exe", _
    "C:\Python39\pythonw.exe", _
    "C:\Python310\pythonw.exe", _
    "C:\Python311\pythonw.exe", _
    "C:\Python312\pythonw.exe", _
    "C:\Python313\pythonw.exe", _
    "C:\Users\" & CreateObject("WScript.Network").UserName & "\AppData\Local\Programs\Python\Python312\pythonw.exe", _
    "C:\Users\" & CreateObject("WScript.Network").UserName & "\AppData\Local\Programs\Python\Python311\pythonw.exe", _
    "C:\Users\" & CreateObject("WScript.Network").UserName & "\AppData\Local\Programs\Python\Python310\pythonw.exe" _
)

pythonwPath = ""
Dim i
For i = 0 To UBound(pythonwCandidates)
    If fso.FileExists(pythonwCandidates(i)) Then
        pythonwPath = pythonwCandidates(i)
        Exit For
    End If
Next

If pythonwPath = "" Then
    ' Try to find pythonw via PATH
    On Error Resume Next
    pythonwPath = shell.Exec("where pythonw").StdOut.ReadLine()
    On Error GoTo 0
End If

If pythonwPath = "" Then
    MsgBox "Python (pythonw.exe) not found. Please install Python and add it to PATH.", vbCritical, "Daily Tracker"
    WScript.Quit 1
End If

' Build the command to run the tracker
trackerScript = scriptDir & "\run_tracker.py"
command = """" & pythonwPath & """ """ & trackerScript & """"

' Run silently (hidden window)
shell.Run command, 0, False

WScript.Quit 0