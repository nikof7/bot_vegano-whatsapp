from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
import urllib3 as urllib
from PIL import Image
import requests
from io import BytesIO
import cv2
from pyzbar.pyzbar import decode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bot.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Iniciar tabla
db = SQLAlchemy(app)

class Productos(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String)
	codigo = db.Column(db.Integer)
	esvegan = db.Column(db.String)
	comentario = db.Column(db.String)

	def __repr__(self):
		return "<Producto %r>" % self.nombre

def img_to_code(url):
    # Busca un producto en la base de datos, utilizando su código de barras.
    response = requests.get(url)
    try:
        img = Image.open(BytesIO(response.content))
        decoding = str(decode(img)[0][0])
        ing_code = decoding.split("'")[1]
    except:
        ing_code = False
    return ing_code

def search_code(inc_code):

	query = Productos.query.filter_by(codigo=inc_code).first()
	
	if query:
		exists = True
		product_name = query.nombre
		is_it_vegan = query.esvegan.lower() 

	if query == None:
		exists = False
		product_name = " "
		is_it_vegan = " "

	return exists, product_name, is_it_vegan

def split_txt(ing_msg_body):
	txt_msg_ = []
	str_splitted = ing_msg_body.split(",")
	for i in str_splitted:
		txt_msg_.append(' '.join(i.split()))
	return txt_msg_

@app.route('/mybot', methods = ['POST', 'GET'])
def mybot():
	
	# Variables de respuesta
	msg_ERROR = "Algo salió mal."
	msg_ERROR_NEW_PRODUCT = "Para crear un nuevo producto debes escribir\nNuevo, titulo, ¿es vegano?, comentario\nEjemplo: Nuevo, Pure de papas Hornex, si, alto en sodio."
	msg_ERROR_READ_IMG = "No se pudo leer la imagen."

	# Variables para manejar los mensajes.
	resp = MessagingResponse()
	msg = resp.message()
	received = request.values
	responded = False
	# Roles
	admins = ("5989896922206","5989296422971")
	inc_phone_number = received.get('WaId')

	# Este if es para que no entre a este código cuando llega el mensaje de 'received' y 'delivered'
	if received.get('SmsStatus') == 'received':	
			
		ing_msg_body = received.get('Body')
		ing_msg_media = received.get('MediaUrl0')
		usr_name = received.get('ProfileName')
		txt_msg = split_txt(ing_msg_body)

		# Texto e imagen para admins
		if ing_msg_body and ing_msg_media and inc_phone_number in admins and not responded:

			# Si el texto empieza con NUEVO, es para agregar un producto.
			if txt_msg[0].lower() == 'nuevo' and len(txt_msg) >=3 and inc_phone_number in admins and not responded:
				
				inc_code = img_to_code(ing_msg_media)

				# Se pudo leer la imagen:
				if inc_code != False and not responded: 
					
					product_info = search_code(inc_code)
					
					# Respuesta a cuando el código se encuentra en la base de datos.
					if product_info[0] ==  True:
						if product_info[2] == "si":
							msg.body(f'¡No se pudo crear el nuevo producto, {product_info[1]} ya se encuentra registrado y es vegano!')
							responded = True
						if product_info[2] == "no":
							msg.body(f'¡No se pudo crear el nuevo producto, {product_info[1]} ya se encuentra registrado y NO es vegano!')
							responded = True
						
					if product_info[0] == False and txt_msg and not responded:
					
						nombre = txt_msg[1]
						esvegan = txt_msg[2]
						codigo = int(inc_code)

						# Este if es porque los comentarios no son obligatorios.
						if len(txt_msg) > 3:
							comentario = txt_msg[3]
						else:
							comentario = "Sin comentarios"

						nuevo_producto = Productos(nombre = nombre, esvegan = esvegan, comentario=comentario, codigo=codigo)

						# Añade el nuevo producto a la base de datos.
						try:
							db.session.add(nuevo_producto)
							db.session.commit()
							msg.body(f'Se agregó el producto {nombre}')
							responded = True
						except:
							msg.body(f'❌ Error al ingresar nuevo producto, prueba nuevamente. ❌')
							responded = True

				# No se pudo leer la imagen.
				if inc_code == False:
					msg.body(msg_ERROR_READ_IMG)
					responded = True

			# Respuesta cuando el texto está mal.
			if not responded:
				msg.body(msg_ERROR_NEW_PRODUCT)
				responded = True

		# Llega imágen, leo el código y devuelvo si está en la base o no (ignoro texto).
		if ing_msg_media and not responded:
			
			# Leo el codigo de barras de la imagen
			inc_code = img_to_code(ing_msg_media)

			# Error al leer la imagen.
			if inc_code == False:
				msg.body(msg_ERROR_READ_IMG)
				responded = True

			if inc_code != False and not responded: 
				product_info = search_code(inc_code)
				if product_info[0] ==  True:
					if product_info[2] == "si":
						msg.body(f'¡El producto: {product_info[1]}  es vegano!')
						responded = True

					if product_info[2] == "no":
						msg.body(f'¡El producto: {product_info[1]} NO es vegano!')
						responded = True

				if product_info[0] == False:
					msg.body('El producto no se encuentra en nuestra base de datos. Si quieres ayudarnos escribe _*"Ayuda"*_')
					responded = True 

			# Por las dudas de que exista algún error.
			if not responded:
				msg.body(msg_ERROR)
				responded = True

		if not ing_msg_media and txt_msg[0].lower() == "modificar" and not responded:
			msg.body("Modificar un archivo")
			responded = True 

		# Solo texto (AYUDA)
		if txt_msg[0].lower() == "ayuda" and not responded:
			msg.body('🌱 Para ayudarte a conocer si un producto es vegano, solo mándanos una foto del _*código de barras*_.\n\n🆘 ¿Quieres ayudar a generar nuestra base de datos?, infórmanos sobre algún producto vegano en este formulario:\nhttps://forms.gle/P7pg5FJSt6dZYFrT9\n\n💰 Si quieres *colaborar* con este emprendimiento, puedes ayudarnos a través de *mercadopago*\nhttps://mpago.la/1G1a9GF')
			responded = True

		# Solo texto
		if not ing_msg_media and not responded:
			msg.body(f'🌱🤖 *{usr_name}*, soy un ```robot vegano``` que te ayuda a conocer qué productos son *aptos*.\n\n📷 Si me envías una foto del *código de barras* del producto, puedo decirte si es vegano o no. Pueden ser alimentos, artículos de higiene personal, cosméticos, etc.\n\nℹ️ Para más información escribe _*"Ayuda"*_.\n\n🌸 Gracias por usar _*botVegano_uy*_ {inc_phone_number}')
			responded = True


		if not responded:
			msg.body(msg_ERROR)
			responded = True

	return str(resp)

if __name__ == "__main__":
	app.run(debug=True)