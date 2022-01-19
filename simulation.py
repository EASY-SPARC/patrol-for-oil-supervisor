from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta

import numpy as np
from fastkml import kml
from shapely import geometry
import shapefile

class Simulation(object):
    def __init__(self, interval, north, south, east, west):

        self._timer     = None
        self.interval   = interval
        self.is_running = False
        self.mission    = None

        self.north = north
        self.south = south
        self.east = east
        self.west = west

        # Instance for gnome interface
        self._gnome = GnomeInterface(north, south, east, west)

        # Read ISL shape file
        isl_shp = shapefile.Reader('./assets/shp/ISL.shp', encoding="ISO8859-1")
        isl_attr = np.array(isl_shp.records())[:, 0] # Gets only isl value
        isl_features = isl_shp.shapeRecords()
        self.isl = np.zeros((len(isl_attr) - len(np.where(isl_attr == 0)[0]), 3)) # [lon, lat, isl_value]
        cnt = 0
        for i in range(len(isl_features)):
            # Each feature has a geo_interface with a list of coordinates representing an ISL value
            if (isl_attr[i] > 0):
                if (isl_features[i].shape.__geo_interface__['type'] == 'LineString'):
                    mean_lon, mean_lat = np.mean(np.array(isl_features[i].shape.__geo_interface__['coordinates']), axis = 0)
                elif (isl_features[i].shape.__geo_interface__['type'] == 'MultiLineString'):
                    aux_list = isl_features[i].shape.__geo_interface__['coordinates']
                    aux_coords = np.vstack([aux_list[j] for j in range(len(aux_list))])
                    mean_lon, mean_lat = np.mean(aux_coords, axis = 0)
                else:
                    print('Unknown type: ' + isl_features[i].shape.__geo_interface__['type'])
                    continue
            
                self.isl[cnt, :] = [mean_lon, mean_lat, isl_attr[i]]
                cnt += 1
               
        # Calculating first simulation step and retrieving particles lon/lat
        self._gnome.step(datetime.now() + timedelta(hours=3)) # -03 GMT timezone
        self.lon, self.lat = self._gnome.get_particles()

   
    def _run(self):        
        # Cyclic code here
        self._gnome.save_particles(self.lon, self.lat)

        #self._gnome.step(datetime(2020, 9, 15, 12, 0, 0))
        self._gnome.step(datetime.now() + timedelta(hours=3)) # -03 GMT timezone

        self.lon, self.lat = self._gnome.get_particles()

        if self.mission != None :

            I1 = np.where(self.lon >= self.mission.minLon)[0]
            lonI = self.lon[I1]
            latI = self.lat[I1]

            I2 = np.where(lonI <= self.mission.maxLon)[0]
            lonI = lonI[I2]
            latI = latI[I2]

            I3 = np.where(latI >= self.mission.minLat)[0]
            lonI = lonI[I3]
            latI = latI[I3]

            I4 = np.where(latI <= self.mission.maxLat)[0]
            lonI = lonI[I4]
            latI = latI[I4]

            self.mission.idx = I1[I2[I3[I4]]]

            self.mission.kde = self.mission._compute_kde(lonI, latI)
            
        # Unlocks timer
        self.is_running = False
        self.start()

    def report_oil(self, lon, lat):
        self._gnome.add_oil(lon, lat)
    
    def get_particles(self, minLon, maxLon, minLat, maxLat):
        # Compute new global idx
        I1 = np.where(self.lon >= minLon)[0]
        lonI = self.lon[I1]
        latI = self.lat[I1]

        I2 = np.where(lonI <= maxLon)[0]
        lonI = lonI[I2]
        latI = latI[I2]

        I3 = np.where(latI >= minLat)[0]
        lonI = lonI[I3]
        latI = latI[I3]

        I4 = np.where(latI <= maxLat)[0]
        lonI = lonI[I4]
        latI = latI[I4]

        #return np.vstack([lonI, latI])
        return np.vstack([self.lon, self.lat])

    def get_isl(self):
        return self.isl
    
    def set_mission(self, mission):
        self.mission = mission

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

