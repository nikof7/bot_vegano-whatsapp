texto = "nuevo,NombreSi, comentario"

hola = "hola,q,andas"

corrigo0 = hola.replace(" ", "")
corrigo1 = texto.replace(" ,", ",")
corrigo2 = corrigo1.replace(", ", ",")
texto_separado = corrigo2.split(",")


print(corrigo0)

if len(texto_separado) >= 2:
    print(f"Hola {texto_separado}")

if len(texto_separado) <= 1:
    print(f"Holan't {texto_separado}")