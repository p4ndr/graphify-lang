VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "ThisWorkbook"
Attribute VB_Base = "0{00020819-0000-0000-C000-000000000046}"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Attribute VB_TemplateDerived = False
Attribute VB_Customizable = True
'==================================================================
' ThisWorkbook - synthetic corpus sample (plan 05 S6.1, M12)
'==================================================================
Option Explicit

Private mOpened As Boolean

Private Sub Workbook_Open()
    mOpened = True
    RefreshStatus
End Sub

Private Sub Workbook_SheetChange(ByVal Sh As Object, ByVal Target As Range)
    If Not mOpened Then Exit Sub
    ValidateCell Target
End Sub

Private Sub RefreshStatus()
    Application.StatusBar = "Ready"
End Sub

Private Sub ValidateCell(ByVal Target As Range)
    If IsEmpty(Target.Value) Then RefreshStatus
End Sub
