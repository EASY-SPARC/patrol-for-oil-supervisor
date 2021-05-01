from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta

import numpy as np
from fastkml import kml
from shapely import geometry
import shapefile

KDE_BW = 0.2        # KDE Bandwidth
RES_GRID = 111.0    # Grid resolution (km in each cell)

class Simulation(object):
    def __init__(self, interval, region):

        self._timer     = None
        self.interval   = interval
        self.is_running = False
        self.mission    = None

        # Instance for gnome interface
        self._gnome = GnomeInterface()

        # Read kml and extract coordinates
        with open(region) as regionFile:
            regionString = regionFile.read()

        regionKML = kml.KML()
        regionKML.from_string(regionString)
        regionPolygon = list(list(list(regionKML.features())[0].features())[0].features())[0].geometry
        (self.minLon, self.minLat, self.maxLon, self.maxLat) = regionPolygon.bounds
        self.coords = np.array(regionPolygon.exterior.coords)

        # Create grid maps based on region boundaries
        self.width = int(np.ceil(RES_GRID * (self.maxLon - self.minLon)))
        self.height = int(np.ceil(RES_GRID * (self.maxLat - self.minLat)))
        
        self.mask = np.zeros((self.height, self.width))

        # Read ISL shape file
        isl_shp = shapefile.Reader('./assets/shp/ISL.shp')
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

        # Filtering ISL
        idx = np.where(self.isl[:, 1] >= self.minLat - 1)[0]
        isl_filtered = self.isl[idx, :]

        idx = np.where(isl_filtered[:, 1] <= self.maxLat + 1)[0]
        isl_filtered = isl_filtered[idx, :]

        # Gaussians ISL-centered as potential fields
        sigma = 0.1
        self.potential_field = np.zeros((self.height, self.width))
        for potential in isl_filtered:
            for i in range(self.width):
                for j in range(self.height):
                    curr_lon = (i/RES_GRID) + self.minLon
                    curr_lat = (j/RES_GRID) + self.minLat

                    Amp = potential[2]
                    lon_0 = potential[0]
                    lat_0 = potential[1]

                    self.potential_field[j, i] += Amp * np.exp(-( \
                        ((curr_lon - lon_0)**2)/(2 * sigma**2) + \
                            ((curr_lat - lat_0)**2)/(2 * sigma**2) \
                                ))

        # Checking which cells are inside the region of interest polygon and calculating distance to nearest point in coast
        for i in range(self.width):
            for j in range(self.height):
                if regionPolygon.intersects(geometry.Point((i/RES_GRID) + self.minLon, (j/RES_GRID) + self.minLat)) == False:
                    self.mask[j, i] = 1
        
        
        max_potential = np.max(self.potential_field)
        self.potential_field = 1/max_potential * 5 * (1 - self.mask) * self.potential_field - self.mask
        
        self.mask_idx = np.argwhere(self.mask.T == 0) # indexes of cells inside polygon
       
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

    def get_env_sensibility(self):
        # return dist_grid # Alternative
        return self.potential_field
    
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

