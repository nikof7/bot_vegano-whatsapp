"""
¿Qué es el botVegano? mandar foto de un código de barras y que responda si es vegano o no.

¿Que se necesita?
	- Una base de datos, donde se tenga si tal producto es vegano o no.
		- ¿Qué parametros debe tener la base de datos?
			- ID
			- Nombre del producto
			- Código de barra del producto
			- Es vegano, si, no, dudoso.
			- Comentarios
"""
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
	img = Image.open(BytesIO(response.content))
	codigo = str(decode(img)[0][0])[2:-1]
	return codigo


@app.route('/mybot', methods = ['POST', 'GET'])
def mybot():
	
	resp = MessagingResponse()
	msg = resp.message()
	recibido = request.values
	responded = False

	# Si es texto
	if 	recibido.get('Body'):
		msg.body("Debes enviar la imagen del código de barras del producto")

	# Si es una imagen
	if 	recibido.get('MediaUrl0'):
		print(request.values)
		# Busco link de la imagen
		url = recibido.get('MediaUrl0')

		print(imagen_a_codigo(url))

		msg.body("mira consola")

		misProductos = db.session.query(Productos).all()
							
		for producto in misProductos:
			if str(producto.codigo) == codigo:
				msg.body(f'¡{producto.nombre} es vegano!')
				responded = True
		

		if not responded:
			msg.body("El producto no es vegano o no se encuentra en nuestra base de datos")"""
						




	return str(resp)

if __name__ == "__main__":
	app.run(debug=True)