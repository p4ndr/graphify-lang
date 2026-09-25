VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmMain 
   Caption         =   "Main"
   OleObjectBlob   =   "frmMain.frx":0000
End
Attribute VB_Name = "frmMain"
Attribute VB_GlobalNameSpace = False
Attribute VB_PredeclaredId = True
Option Explicit

Private mShape As clsCircle

Private Sub UserForm_Initialize()
    Set mShape = New clsCircle
    mShape.Radius = 2
    Util.Run
End Sub
