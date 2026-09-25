Option Explicit

Private mName As String

Public Sub Init(ByVal name As String)
    Dim trimmed As String
    trimmed = Trim$(name)
    mName = trimmed
End Sub

Public Function Name() As String
    Name = mName
End Function
