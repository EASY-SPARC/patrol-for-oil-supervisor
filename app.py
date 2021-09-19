from flask import Flask, request, jsonify, make_response, Response
from flask import render_template
from flask_restx import Api, Resource, fields

from datetime import datetime, timedelta

import numpy as np
import json
import os

from simulation import Simulation
from weather_conditions import WeatherConditions
from mission import Mission

flask_app = Flask(__name__)

# Configuring polygon upload folder
UPLOAD_FOLDER = './assets/'
flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# RESTful APis
app = Api(app = flask_app, 
		  version = "1.0", 
		  title = "Patrol for oil APIs", 
		  description = "Service APIs for the patrol for oil application.")

ns_config = app.namespace('config', description='Simulation and Mission configuration APIs')
ns_robot_fb = app.namespace('robot_fb', description='Robot feedback APIs')
ns_report_oil = app.namespace('report_oil', description='Report Oil APIs')
ns_simulation = app.namespace('simulation', description='Simulation variables APIs')
ns_mission = app.namespace('mission', description='Mission variables APIs')

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

model_mission_conf = app.model('Configure mission', {
		'region': fields.String(required = True, description = "Region of interest polygon"),
		't_mission': fields.Float(required = True, description = "Time for mission"),
		'n_robots': fields.Integer(required = True, description = "Number of robots in mission"),
		'robots_weights': fields.List(fields.List(fields.Float), required = False, description = "List of weights for reactive patrolling strategy")
	})

model_simul_conf = app.model('Conf Simulation params', {
		't_g': fields.Float(required = True, description="Time interval for gnome simulation"),
		't_w': fields.Float(required = True, description="Time interval for weather parameters update"),
		'north': fields.Float(required = False, description="Simulation area max latitude"),
		'south': fields.Float(required = False, description="Simulation area min latitude"),
		'east': fields.Float(required = False, description="Simulation area max longitude"),
		'west': fields.Float(required = False, description="Simulation area min longitude")
	})

# Default values for simulation and mission parameters
t_g = 3 * 60			# time step simulation (seconds)
t_w = 24 * 60 * 60		# time step to download new weather data (seconds)
north = -8.5
south = -11
east = -34
west = -36.5

t_mission = 0
robots = []
region = None

simulation = None
weatherConditions = None
mission = None

# HTML rendering
@flask_app.route('/index', methods=['GET'])
def display_index():
	if (simulation == None):
		return display_config_simul()
	else:
		return display_viz()

@flask_app.route('/viz', methods=['POST'])
def display_viz():
	global mission

	configured_mission = False if mission == None else True

	return render_template('viz.html', configured_mission=configured_mission)

@flask_app.route('/config_simul', methods=['POST'])
def display_config_simul():
	return render_template('config_simul.html', \
		t_g=t_g/60, t_w=t_w/(24*60*60), minLon=west, maxLon=east, minLat=south, maxLat=north)

@flask_app.route('/start', methods=['POST'])
def display_started():
	global simulation
	global weatherConditions
	global t_g, t_w, north, south, east, west

	t_g = float(request.form['t_g']) * 60
	t_w = float(request.form['t_w']) * 24 * 60 * 60
	north = float(request.form['north'])
	south = float(request.form['south'])
	east = float(request.form['east'])
	west = float(request.form['west'])

	if (weatherConditions == None):
		weatherConditions = WeatherConditions(t_w, north, south, east, west)
		
	weatherConditions.start()

	if (simulation == None):
		simulation = Simulation(t_g)
	
	simulation.start()

	return display_viz()

@flask_app.route('/config_mission', methods=['POST'])
def display_config_mission():

	return render_template('config_mission.html', \
		robots=robots, region=region, t_mission=t_mission)

@flask_app.route('/saved_mission', methods=['POST'])
def display_stoped():
	global mission
	global t_mission, robots, region

	t_mission = float(request.form['t_mission'])
	n_robots = int(request.form['n_robots'])
	robots = []

	region = request.files['region']
	regionFilename = './assets/region.kml'
	region.save(regionFilename)

	for i in range(n_robots):
		kappa = float(request.form['kappa_'+str(i+1)])
		omega_c = float(request.form['omega_c'+str(i+1)])
		omega_s = float(request.form['omega_s'+str(i+1)])
		omega_d = float(request.form['omega_d'+str(i+1)])
		omega_n = float(request.form['omega_n'+str(i+1)])
		robots.append({'id': (i+1), 'pos_x': 0, 'pos_y': 0, 'heading': 0, 'kappa': kappa, 'omega_c': omega_c, 'omega_s': omega_s, 'omega_d': omega_d, 'omega_n': omega_n})

	mission = Mission(t_mission, robots, regionFilename, simulation)

	simulation.set_mission(mission)

	return display_viz()

# API requests
@ns_config.route("/simlation")
class MainClass(Resource):
	@app.expect(model_simul_conf)		
	def post(self):
		try: 
			formData = request.json
			t_g = formData['t_g']
			t_w = formData['t_w']
			north = formData['north']
			south = formData['south']
			east = formData['east']
			west = formData['west']
			
			response = jsonify({
				"statusCode": 200,
				"status": "Simulation config applied",
				"result": "ok"
				})
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response
		except Exception as error:
			return jsonify({
				"statusCode": 500,
				"status": "Could not apply configuration",
				"error": str(error)
			})

@ns_config.route("/mission")
class MainClass(Resource):
	@app.expect(model_mission_conf)		
	def post(self):
		try: 
			formData = request.json
			region = formData['region']
			t_mission = formData['t_mission']
			n_robots = formData['n_robots']
			robots_weights = formData['robots_weights']
			
			response = jsonify({
				"statusCode": 200,
				"status": "Mission config applied",
				"result": "ok"
				})			
			response.headers.add('Access-Control-Allow-Origin', '*')
			return response
		except Exception as error:
			return jsonify({
				"statusCode": 500,
				"status": "Could not apply configuration",
				"error": str(error)
			})

@ns_robot_fb.route("/")
class MainClass(Resource):
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

			mission.robot_feedback(robot_id, xgrid, ygrid, robot_heading, lon, lat)
			
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


@ns_mission.route("/kde")
class MainClass(Resource):
	def get(self):
		kde = mission.get_kde()
		response = jsonify({
				"statusCode": 200,
				"kde": kde.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_simulation.route("/env_sensibility")
class MainClass(Resource):
	def get(self):
		env_sensibility = simulation.get_env_sensibility()
		response = jsonify({
				"statusCode": 200,
				"env_sensibility": env_sensibility.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_simulation.route('/isl')
class MainClass(Resource):
	def get(self):
		isl = simulation.get_isl()
		response = jsonify({
				"statusCode": 200,
				"isl": isl.tolist()
			})
		
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_simulation.route("/particles/minLon:<minLon>&maxLon:<maxLon>&minLat:<minLat>&maxLat:<maxLat>")
@ns_simulation.param('minLon', 'Min Longitude')
@ns_simulation.param('maxLon', 'Max Longitude')
@ns_simulation.param('minLat', 'Min Latitude')
@ns_simulation.param('maxLat', 'Max Latitude')
class MainClass(Resource):
	def get(self, minLon, maxLon, minLat, maxLat):
		particles = simulation.get_particles(float(minLon), float(maxLon), float(minLat), float(maxLat))
		response = jsonify({
				"statusCode": 200,
				"particles": particles.tolist()
			})
		
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_mission.route("/robots_pos")
class MainClass(Resource):
	def get(self):
		robots_pos = mission.get_robots_pos()
		robots_heading = mission.get_robots_heading()
		response = jsonify({
				"statusCode": 200,
				"robots_pos": robots_pos.tolist(),
				"robots_heading": robots_heading.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_mission.route("/robots_lon_lat")
class MainClass(Resource):
	def get(self):
		robots_lon_lat = mission.get_robots_lon_lat()
		robots_heading = mission.get_robots_heading()
		response = jsonify({
				"statusCode": 200,
				"robots_lon_lat": robots_lon_lat.tolist(),
				"robots_heading": robots_heading.tolist()
			})
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_mission.route('/region')
class MainClass(Resource):
	def get(self):
		region = mission.get_region()
		response = jsonify({
				"statusCode": 200,
				"region": region.tolist()
			})
		
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response

@ns_mission.route('/robots_weights')
class MainClass(Resource):
	def get(self):
		weights = mission.get_robots_weights()
		response = jsonify({
				"statusCode": 200,
				"weights": weights.tolist()
			})
		
		response.headers.add('Access-Control-Allow-Origin', '*')
		return response