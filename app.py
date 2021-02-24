from flask import Flask, request, jsonify, make_response, Response
from flask_restplus import Api, Resource, fields

from datetime import datetime, timedelta

import numpy as np
import json

from simulation import Simulation

flask_app = Flask(__name__)
app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Patrol for oil", 
		  description = "Service for the patrol for oil application.")

ns_robot_fb = app.namespace('robot_fb', description='Robot feedback APIs')
ns_report_oil = app.namespace('report_oil', description='Report Oil APIs')
ns_kde = app.namespace('kde', description='Kernel Density Estimation APIs')
ns_env_sensibility = app.namespace('env_sensibility', description='Environmental Sensibility APIs')

model_robot_fb = app.model('Robot feedback params', {
		'xgrid': fields.String(required = True, description="x robot position", help="Can not be blank"),
		'ygrid': fields.String(required = True, description="y robot position", help="Can not be blank"),
		'lon': fields.String(required = False, description="lon coordinates for sensed oil particles", help="Can be blank"),
		'lat': fields.String(required = False, description="lat coordinates for sensed oil particles",  help="Can be blank")
	})

model_report_oil = app.model('Report Oil params', {
		'lon': fields.String(required = True, description="lon coordinates for sensed oil particles", help="Can not be blank"),
		'lat': fields.String(required = True, description="lat coordinates for sensed oil particles",  help="Can not be blank")
	})

t_g = 3 * 60

simulation = Simulation(t_g, 'assets/region.kml')
simulation.start()

@ns_robot_fb.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	@app.expect(model_robot_fb)		
	def post(self):
		try: 
			formData = request.json
			simulation.robot_feedback(formData['xgrid'], formData['ygrid'], formData['lon'], formData['lat'])
			
			response = jsonify({
				"statusCode": 200,
				"status": "Robot feedback applied",
				"result": "ok"
				})			
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response
		except Exception as error:
			return jsonify({
				"statusCode": 500,
				"status": "Could not apply robot feedback",
				"error": str(error)
			})

@ns_report_oil.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	@app.expect(model_report_oil)		
	def post(self):
		try: 
			formData = request.json
			simulation.robot_feedback(formData['xgrid'], formData['ygrid'], formData['lon'], formData['lat'])
			
			response = jsonify({
				"statusCode": 200,
				"status": "Robot feedback applied",
				"result": "ok"
				})			
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response
		except Exception as error:
			return jsonify({
				"statusCode": 500,
				"status": "Could not apply robot feedback",
				"error": str(error)
			})


@ns_kde.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	def get(self):
		kde = simulation.get_kde()
		return jsonify({
				"statusCode": 200,
				"kde": kde.tolist()
			})

@ns_env_sensibility.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	def get(self):
		kde = simulation.get_kde()
		return jsonify({
				"statusCode": 200,
				"kde": kde.tolist()
			})