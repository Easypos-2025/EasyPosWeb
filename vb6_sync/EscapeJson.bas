' ============================================================
' EscapeJson
' Escapa caracteres especiales para producir JSON válido.
' Agregar esta función al módulo de utilidades del proyecto VB6.
'
' Maneja en un solo paso (para no doble-escapar):
'   Chr(92)  \    → \\
'   Chr(34)  "    → \"
'   Chr(9)   Tab  → \t
'   Chr(10)  LF   → \n
'   Chr(13)  CR   → \r
'   Chr(0)–Chr(8), Chr(11)–Chr(12), Chr(14)–Chr(31)
'            caracteres de control — se descartan (JSON no los admite sin escape)
' ============================================================
Public Function EscapeJson(s As String) As String
    Dim r As String
    Dim i As Integer
    Dim c As String
    Dim code As Integer

    r = ""
    For i = 1 To Len(s)
        c = Mid(s, i, 1)
        code = Asc(c)
        Select Case code
            Case 92             ' backslash — primero para no doble-escapar
                r = r & "\\"
            Case 34             ' comilla doble
                r = r & "\"""
            Case 9              ' Tab
                r = r & "\t"
            Case 10             ' LF
                r = r & "\n"
            Case 13             ' CR
                r = r & "\r"
            Case 0 To 31        ' resto de control chars — descartar
                ' Chr(0) NULL byte, Chr(1-8), Chr(11-12), Chr(14-31)
            Case Else           ' carácter normal (>= 32)
                r = r & c
        End Select
    Next i

    EscapeJson = r
End Function
