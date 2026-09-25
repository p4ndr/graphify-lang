VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "clsCircle"
Option Explicit
Implements IShape

Private mRadius As Double

Public Property Get Radius() As Double
    Radius = mRadius
End Property

Public Property Let Radius(ByVal value As Double)
    mRadius = value
End Property

Private Sub IShape_Render()
    WriteLog "r=" & Area(mRadius)
End Sub
