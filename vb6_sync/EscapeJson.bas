' ============================================================
' EscapeJson
' Escapa caracteres especiales para producir JSON válido.
' Agregar esta función al módulo de utilidades del proyecto VB6.
' ============================================================
Public Function EscapeJson(s As String) As String
    Dim r As String
    r = s
    r = Replace(r, "\",  "\\")   ' primero, para no doble-escapar
    r = Replace(r, """", "\""")
    r = Replace(r, Chr(13), "\r")
    r = Replace(r, Chr(10), "\n")
    r = Replace(r, Chr(9),  "\t")
    EscapeJson = r
End Function
