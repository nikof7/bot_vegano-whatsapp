
def separa_texto(text):
    corrigo1 = text.replace(" ,", ",")
    corrigo2 = corrigo1.replace(", ", ",")
    texto_separado = corrigo2.split(",")
    return texto_separado

a = separa_texto("Nuevo, titulo, si")

print(len(a))