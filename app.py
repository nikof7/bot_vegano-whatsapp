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

def imagen_a_codigo(url):
    # Busca un producto, utilizando su código de barras, en la base de datos.
    response = requests.get(url)
    try:
        img = Image.open(BytesIO(response.content))
        decoding = str(decode(img)[0][0])
        incoming_codigo = decoding.split("'")[1]
    except:
        incoming_codigo = False
    return incoming_codigo

def busca_codigo(codigo_leido):

	consulta = Productos.query.filter_by(codigo=codigo_leido).first()
	
	if consulta:
		nombreProducto = consulta.nombre
		esveganProducto = consulta.esvegan.lower() 
		existe = True

	if consulta == None:
		nombreProducto = " "
		esveganProducto = " "
		existe = False

	return existe, nombreProducto, esveganProducto

def separa_texto(incoming_msg_body):
	corrigo1 = incoming_msg_body.replace(" ,", ",")
	corrigo2 = corrigo1.replace(", ", ",")
	texto_separado = corrigo2.split(",")
	return texto_separado

@app.route('/mybot', methods = ['POST', 'GET'])
def mybot():
	
	# Variables de respuesta
	msg_ERROR = "Algo salió mal."
	msg_ERROR_NUEVO_PRODUCTO_TEXTO = "Para crear un nuevo producto debes escribir\nNuevo, titulo, ¿es vegano?, comentario\nEjemplo: Nuevo, Pure de papas Hornex, si, alto en sodio."
	msg_ERROR_LEER_IMAGEN = "No se pudo leer la imagen."

	# Variables para manejar los mensajes.
	resp = MessagingResponse()
	msg = resp.message()
	recibido = request.values
	responded = False

	# Roles
	administradores = ("59898969206","5989879672061111")
	es_admin = recibido.get('WaId')

	# Este if es para que no entre a este código cuando llega el mensaje de 'received' y 'delivered'
	if recibido.get('SmsStatus') == 'received':	
			
		incoming_msg_body = recibido.get('Body')
		incoming_msg_media = recibido.get('MediaUrl0')
		nombre_usuario = recibido.get('ProfileName')
		texto_separado = separa_texto(incoming_msg_body)

		# Texto e imagen para administradores
		if incoming_msg_body and incoming_msg_media and es_admin in administradores and not responded:

			# Si el texto empieza con NUEVO, es para agregar un producto.
			if texto_separado[0].lower() == 'nuevo' and len(texto_separado) >=3 and es_admin in administradores and not responded:
				
				codigo_leido = imagen_a_codigo(incoming_msg_media)

				# Se pudo leer la imagen:
				if codigo_leido != False and not responded: 
					
					codigo_existe = busca_codigo(codigo_leido)
					
					# Respuesta a cuando el código se encuentra en la base de datos.
					if codigo_existe[0] ==  True:
						if codigo_existe[2] == "si":
							msg.body(f'¡No se pudo crear el nuevo producto, {codigo_existe[1]} ya se encuentra registrado y es vegano!')
							responded = True
						if codigo_existe[2] == "no":
							msg.body(f'¡No se pudo crear el nuevo producto, {codigo_existe[1]} ya se encuentra registrado y NO es vegano!')
							responded = True
						
					if codigo_existe[0] == False and texto_separado and not responded:
					
						nombre = texto_separado[1]
						esvegan = texto_separado[2]
						codigo = int(codigo_leido)

						# Este if es porque los comentarios no son obligatorios.
						if len(texto_separado) > 3:
							comentario = texto_separado[3]
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
				if codigo_leido == False:
					msg.body(msg_ERROR_LEER_IMAGEN)
					responded = True

			# Respuesta cuando el texto está mal.
			if not responded:
				msg.body(msg_ERROR_NUEVO_PRODUCTO_TEXTO)
				responded = True

		# Llega imágen, leo el código y devuelvo si está en la base o no (ignoro texto).
		if incoming_msg_media and not responded:
			
			# Leo el codigo de barras de la imagen
			codigo_leido = imagen_a_codigo(incoming_msg_media)

			# Error al leer la imagen.
			if codigo_leido == False:
				msg.body(msg_ERROR_LEER_IMAGEN)
				responded = True

			if codigo_leido != False and not responded: 
				codigo_existe = busca_codigo(codigo_leido)
				if codigo_existe[0] ==  True:
					if codigo_existe[2] == "si":
						msg.body(f'¡El producto: {codigo_existe[1]}  es vegano!')
						responded = True

					if codigo_existe[2] == "no":
						msg.body(f'¡El producto: {codigo_existe[1]} NO es vegano!')
						responded = True

				if codigo_existe[0] == False:
					msg.body('no está en la base')
					responded = True 

			# Por las dudas de que exista algún error.
			if not responded:
				msg.body(msg_ERROR)
				responded = True

		if not incoming_msg_media and texto_separado[0].lower() == "modificar" and not responded:
			msg.body("Modificar un archivo")
			responded = True 

		# Solo texto (AYUDA)
		if texto_separado[0].lower() == "ayuda" and not responded:
			msg.body('🌱 Para ayudarte a conocer si un producto es vegano, solo mándanos una foto del _*código de barras*_.\n\n🆘 ¿Quieres ayudar a generar nuestra base de datos?, infórmanos sobre algún producto vegano en este formulario:\nhttps://forms.gle/P7pg5FJSt6dZYFrT9\n\n💰 Si quieres *colaborar* con este emprendimiento, puedes ayudarnos a través de *mercadopago*\nhttps://mpago.la/1G1a9GF')
			responded = True

		# Solo texto
		if not incoming_msg_media and not responded:
			msg.body(f'🌱🤖 *{nombre_usuario}*, soy un ```robot vegano``` que te ayuda a conocer qué productos son *aptos*.\n\n📷 Si me envías una foto del *código de barras* del producto, puedo decirte si es vegano o no. Pueden ser alimentos, artículos de higiene personal, cosméticos, etc.\n\nℹ️ Para más información escribe _*"Ayuda"*_.\n\n🌸 Gracias por usar _*botVegano_uy*_  🌸')
			responded = True


		if not responded:
			msg.body(msg_ERROR)
			responded = True

	return str(resp)

if __name__ == "__main__":
	app.run(debug=True)