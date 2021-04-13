from flask import Flask, request, jsonify, make_response, Response
from flask_restplus import Api, Resource, fields

from datetime import datetime, timedelta

import numpy as np
import json

from simulation import Simulation
from weather_conditions import WeatherConditions

flask_app = Flask(__name__)
app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Patrol for oil APIs", 
		  description = "Service APIs for the patrol for oil application.")

ns_robot_fb = app.namespace('robot_fb', description='Robot feedback APIs')
ns_report_oil = app.namespace('report_oil', description='Report Oil APIs')
ns_kde = app.namespace('kde', description='Kernel Density Estimation APIs')
ns_env_sensibility = app.namespace('env_sensibility', description='Environmental Sensibility APIs')
ns_robots_pos = app.namespace('robots_pos', description='Robots Last Known positions APIs')
ns_particles = app.namespace('particles', description='Particles APIs')
ns_variables = app.namespace('simulation', description='Simulation variables APIs')

model_robot_fb = app.model('Robot feedback params', {
		'robot_id': fields.String(required = True, description="Robot ID", help="Can not be blank"),
		'xgrid': fields.String(required = True, description="x robot position", help="Can not be blank"),
		'ygrid': fields.String(required = True, description="y robot position", help="Can not be blank"),
		'robot_heading': fields.String(required = True, description="Robot heading", help="Can not be blank"),
		'lon': fields.String(required = False, description="lon coordinates for sensed oil particles", help="Can be blank"),
		'lat': fields.String(required = False, description="lat coordinates for sensed oil particles",  help="Can be blank")
	})

model_report_oil = app.model('Report Oil params', {
		'lon': fields.String(required = True, description="lon coordinates for sensed oil particles", help="Can not be blank"),
		'lat': fields.String(required = True, description="lat coordinates for sensed oil particles",  help="Can not be blank")
	})

t_g = 3 * 60			# time step simulation (seconds)
t_w = 24 * 60 * 60		# time step to download new weather data (seconds)

weatherConditions = WeatherConditions(t_w)
weatherConditions.start()

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
			robot_id = int(formData['robot_id'])
			xgrid = int(formData['xgrid'])
			ygrid = int(formData['ygrid'])
			robot_heading = float(formData['robot_heading'])
			if formData['lon'] != '':
				lon = np.fromstring(formData['lon'].replace('[', '').replace(']', ''), dtype=float, sep=',')
			if formData['lat'] != '':
				lat = np.fromstring(formData['lat'].replace('[', '').replace(']', ''), dtype=float, sep=',')

			simulation.robot_feedback(robot_id, xgrid, ygrid, robot_heading, lon, lat)
			
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
			lon = np.fromstring(formData['lon'].replace('[', '').replace(']', ''), dtype=float, sep=',')
			lat = np.fromstring(formData['lat'].replace('[', '').replace(']', ''), dtype=float, sep=',')
			simulation.report_oil(lon, lat)
			
			response = jsonify({
				"statusCode": 200,
				"status": "Oil report registered",
				"result": "ok"
				})			
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response
		except Exception as error:
			return jsonify({
				"statusCode": 500,
				"status": "Could not apply oil report",
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
		response = jsonify({
				"statusCode": 200,
				"kde": kde.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_env_sensibility.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	def get(self):
		env_sensibility = simulation.get_env_sensibility()
		response = jsonify({
				"statusCode": 200,
				"env_sensibility": env_sensibility.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_robots_pos.route("/")
class MainClass(Resource):

	def options(self):
		response = make_response()
		response.headers.add("Access-Control-Allow-Origin", "*")
		response.headers.add('Access-Control-Allow-Headers', "*")
		response.headers.add('Access-Control-Allow-Methods', "*")
		return response

	def get(self):
		robots_pos = simulation.get_robots_pos()
		robots_heading = simulation.get_robots_heading()
		response = jsonify({
				"statusCode": 200,
				"robots_pos": robots_pos.tolist(),
				"robots_heading": robots_heading.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_variables.route('/region/')
class MainClass(Resource):
	def get(self):
		region = simulation.get_region()
		response = jsonify({
				"statusCode": 200,
				"region": region.tolist()
			})
		
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_variables.route("/robots_pos/")
class MainClass(Resource):
	def get(self):
		robots_pos = simulation.get_robots_pos()
		robots_heading = simulation.get_robots_heading()
		response = jsonify({
				"statusCode": 200,
				"robots_pos": robots_pos.tolist(),
				"robots_heading": robots_heading.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_variables.route("/particles/minLon:<minLon>&maxLon:<maxLon>&minLat:<minLat>&maxLat:<maxLat>")
@ns_variables.param('minLon', 'Min Longitude')
@ns_variables.param('maxLon', 'Max Longitude')
@ns_variables.param('minLat', 'Min Latitude')
@ns_variables.param('maxLat', 'Max Latitude')
class MainClass(Resource):
	def get(self, minLon, maxLon, minLat, maxLat):
		particles = simulation.get_particles(float(minLon), float(maxLon), float(minLat), float(maxLat))
		response = jsonify({
				"statusCode": 200,
				"particles": particles.tolist()
			})
		
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response