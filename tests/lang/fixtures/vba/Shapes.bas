Attribute VB_Name = "Shapes"
Option Explicit

#If VBA7 Then
Private Declare PtrSafe Function GetTickCount Lib "kernel32" () As Long
#End If

Public Type Point
    X As Double
    Y As Double
End Type

Public Enum ShapeKind
    skCircle = 1
    skSquare = 2
End Enum

Private mCount As Long

' Draw(x) is only mentioned in this comment
Public Sub Draw(ByVal shape As IShape, _
                Optional ByVal label As String = "Helper(1)")
    Dim c As New clsCircle
    Dim p As Point
    Rem Helper would be a call here, but this is a comment
    mCount = mCount + 1: Helper
    shape.Render
    c.Radius = Len(label)
    Debug.Print "Draw: " & Trim$(label), GetTickCount
End Sub

Private Sub Helper()
    WriteLog "helper"
End Sub

Public Function Area(ByVal r As Double) As Double
    Area = 3.14159 * r * r
End Function

Sub WriteLog(ByVal msg As String)
    Debug.Print msg
End Sub
