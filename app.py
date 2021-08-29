from pyzbar.pyzbar import decode
import cv2
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.messaging_response import MessagingResponse
import urllib3 as urllib
from PIL import Image
import requests
from io import BytesIO
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
	
	resp = MessagingResponse()
	msg = resp.message()
	recibido = request.values
	responded = False
	administradores = ("59898969206","598987967206")
	es_admin = recibido.get('WaId')
	
	# Este if es para que no entre a este código cuando llega el mensaje de 'received' y 'delivered'
	if recibido.get('SmsStatus') == 'received':	
			
		incoming_msg_body = recibido.get('Body')
		incoming_msg_media = recibido.get('MediaUrl0')
		texto_separado = separa_texto(incoming_msg_body)

		# Llega imágen, leo el código y devuelvo si está en la base o no (ignoro texto).
		if incoming_msg_media and not responded and texto_separado[0].lower() != "nuevo":
			
			# Leo el codigo de barras de la imagen
			codigo_leido = imagen_a_codigo(incoming_msg_media)
			if codigo_leido == False:
				msg.body('Asegurate de que la imágen se vea bien.')
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

			if not responded:
				msg.body(f'El producto no se encuentra en nuestra base de datos, si quieres agregarlo puedes ayudarnos en -> shorturl.at/fovH8 {incoming_msg_media}     {codigo_existe}')
				responded = True

		# Solo texto
		if not incoming_msg_media and not responded:
			msg.body('Para comprobar si un producto es vegano, mandanos una foto del código de barras.')			
			responded = True

		# Texto e imagen para administradores
		if incoming_msg_body and incoming_msg_media and es_admin in administradores and not responded:

			# Si el texto empieza con NUEVO, es para agregar un producto.
			if texto_separado[0].lower() == 'nuevo' and es_admin in administradores and not responded:
				
				codigo_leido = imagen_a_codigo(incoming_msg_media)

				if codigo_leido != False and not responded: 
					codigo_existe = busca_codigo(codigo_leido)
					if codigo_existe[0] ==  True:
						if codigo_existe[2] == "si":
							msg.body(f'¡No se pudo crear el nuevo producto, {codigo_existe[1]} ya se encuentra registrado y es vegano!')
							responded = True
						if codigo_existe[2] == "no":
							msg.body(f'¡No se pudo crear el nuevo producto, {codigo_existe[1]} ya se encuentra registrado y NO es vegano!')
							responded = True
						
					if codigo_existe[0] == False and texto_separado not responded:
					
						nombre = texto_separado[1]
						esvegan = texto_separado[2]
						codigo = int(incoming_codigo)

						# Este if es porque los comentarios no son obligatorios
						if len(texto_separado) > 3:
							comentario = texto_separado[3]
						else:
							comentario = "Sin comentarios"

						nuevo_producto = Productos(nombre = nombre, esvegan = esvegan, comentario=comentario, codigo=codigo)

						# Añade el nuevo producto a la base de datos.
						try:
							db.session.add(nuevo_producto)
							db.session.commit()
							msg.body(f'Se agregó el producto "{nombre}"')
							responded = True
						except:
							msg.body(f'❌ Error al ingresar nuevo producto, prueba nuevamente. ❌')
							responded = True

				if codigo_leido == False:
					msg.body('No se pudo leer la imágen')
					responded = True

			if not responded:
				msg.body('Para crear un nuevo producto debes escribir\nNuevo, titulo, ¿es vegano?, comentario\nEjemplo: Nuevo, Pure de papas Hornex, si, alto en sodio')
				responded = True

		if not responded:
			msg.body(f'Por favor, inténtalo de nuevo.1')
			responded = True

	responded = True
	return str(resp)

if __name__ == "__main__":
	app.run(debug=True)