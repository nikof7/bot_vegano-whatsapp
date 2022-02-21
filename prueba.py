if product_info[0] == False and txt_msg and not responded:

	name = txt_msg[1]
	isvegan = txt_msg[2]
	code = int(inc_code)

	# Este if es porque los comentarios no son obligatorios.
	if len(txt_msg) > 3:
		comment = txt_msg[3]
	else:
		comment = " - "

	nuevo_producto = Products(name = name, code=code, isvegan = isvegan, comment=comment)

	# Añade el nuevo producto a la base de datos.
	try:
		db.session.add(nuevo_producto)
		db.session.commit()
		msg.body(f'Se agregó el producto {name}')
		responded = True
	except:
		msg.body(f'❌ Error al ingresar nuevo producto, prueba nuevamente. ❌')
		responded = True


"""--------------------------"""

if product_info[0] ==  True and not responded:
	isvegan = txt_msg[1]
	code = int(inc_code)
	change_product(inc_code = code, is_vegan = isvegan)




	msg.body(f'Se va a modificar el producto {product_info[1]}, con parámetro vegano {product_info[2]} a {txt_msg[1]}')
	responded = True
	