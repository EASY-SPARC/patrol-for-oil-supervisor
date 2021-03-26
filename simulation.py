from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta

from scipy.stats import gaussian_kde

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

        # Instance for gnome interface
        self._gnome = GnomeInterface()

        # Read kml and extract coordinates
        with open(region) as regionFile:
            regionString = regionFile.read()

        regionKML = kml.KML()
        regionKML.from_string(regionString)
        regionPolygon = list(list(list(regionKML.features())[0].features())[0].features())[0].geometry
        (self.minLon, self.minLat, self.maxLon, self.maxLat) = regionPolygon.bounds
        coords = np.array(regionPolygon.exterior.coords)

        # Create grid maps based on region boundaries
        self.width = int(np.ceil(RES_GRID * (self.maxLon - self.minLon)))
        self.height = int(np.ceil(RES_GRID * (self.maxLat - self.minLat)))
        
        self.mask = np.zeros((self.height, self.width))
        self.dist_grid = np.zeros((self.height, self.width))

        # Read shape file
        shpfile = shapefile.Reader('./assets/shp/BRA_admin_AL.shp')
        feature = shpfile.shapeRecords()[0]
        first = feature.shape.__geo_interface__
        shp = geometry.shape(first)
        al_coords = np.array(shp.geoms[3].exterior.coords)

        # Checking which cells are inside the region of interest polygon and calculation distance to nearest point in coast
        for i in range(self.width):
            for j in range(self.height):
                if regionPolygon.intersects(geometry.Point((i/RES_GRID) + self.minLon, (j/RES_GRID) + self.minLat)) == False:
                    self.mask[j, i] = 1
                else:
                    dist = np.sqrt(((i/RES_GRID) + self.minLon - al_coords[:, 0])**2 + ((j/RES_GRID) + self.minLat - al_coords[:, 1])**2)
                    self.dist_grid[j, i] = RES_GRID * np.min(dist)
        
        self.mask_idx = np.argwhere(self.mask.T == 0) # indexes of cells inside polygon
        
        # Calculating first simulation step and retrieving particles lon/lat
        #self._gnome.step(datetime(2020, 9, 15, 12, 0, 0))
        self._gnome.step(datetime.now() + timedelta(hours=3)) # -03 GMT timezone
        self.lon, self.lat = self._gnome.get_particles()

        # Filtering particles to square domain and saving its indexes for later use
        I1 = np.where(self.lon >= self.minLon)[0]
        lonI = self.lon[I1]
        latI = self.lat[I1]

        I2 = np.where(lonI <= self.maxLon)[0]
        lonI = lonI[I2]
        latI = latI[I2]

        I3 = np.where(latI >= self.minLat)[0]
        lonI = lonI[I3]
        latI = latI[I3]

        I4 = np.where(latI <= self.maxLat)[0]
        lonI = lonI[I4]
        latI = latI[I4]

        self.idx = I1[I2[I3[I4]]]

        # Computing kde with filtered particles
        self.kde = self._compute_kde(lonI, latI)

        # Environmental Sensitivity grid values
        max_dist = np.max(self.dist_grid)
        self.dist_grid = 1/max_dist * 5 * ((1 - self.mask) * max_dist - self.dist_grid) + (-self.mask)

        # Initializing robots positions in grid map
        #self.robots_pos = np.empty(shape=[0,2], dtype=int)
        self.robots_pos = np.zeros((10, 2), dtype=int)
        self.robots_heading = np.zeros((10, 1), dtype=float)

        # For tests
        self.robots_pos[0, :] = [1, 16] 
        self.robots_pos[1, :] = [1, 17] 

    def _run(self):        
        # Cyclic code here
        self._gnome.save_particles(self.lon, self.lat)

        #self._gnome.step(datetime(2020, 9, 15, 12, 0, 0))
        self._gnome.step(datetime.now() + timedelta(hours=3)) # -03 GMT timezone

        self.lon, self.lat = self._gnome.get_particles()

        I1 = np.where(self.lon >= self.minLon)[0]
        lonI = self.lon[I1]
        latI = self.lat[I1]

        I2 = np.where(lonI <= self.maxLon)[0]
        lonI = lonI[I2]
        latI = latI[I2]

        I3 = np.where(latI >= self.minLat)[0]
        lonI = lonI[I3]
        latI = latI[I3]

        I4 = np.where(latI <= self.maxLat)[0]
        lonI = lonI[I4]
        latI = latI[I4]

        self.idx = I1[I2[I3[I4]]]

        self.kde = self._compute_kde(lonI, latI)
        
        # Unlocks timer
        self.is_running = False
        self.start()
        
    def _compute_kde(self, lon, lat):
        print('Computing new KDE')
        kde = -1 * self.mask # No Fly Zones cells are -1 valued
    
        h, yEdges, xEdges = np.histogram2d(x=lat, y=lon, bins=[self.height, self.width])

        xls = np.mean(np.array([xEdges[0:-1], xEdges[1:]]), axis=0)
        yls = np.mean(np.array([yEdges[0:-1], yEdges[1:]]), axis=0)
        xx, yy = np.meshgrid(xls, yls)

        #positions = np.vstack([xx.T.ravel(), yy.T.ravel()]).T
        positions = np.vstack([xx.ravel(), yy.ravel()])

        binX, binY = self._get_bins(lon, lat, xEdges, yEdges)

        lonp = np.array([], dtype='float64')
        latp = np.array([], dtype='float64')

        # Find which particles are inside the polygon
        for i in range(self.mask_idx.shape[0]):
            idxs = np.where(np.logical_and(binX == self.mask_idx[i, 0], binY == self.mask_idx[i, 1]))[0]
            lonp = np.append(lonp, lon[idxs])
            latp = np.append(latp, lat[idxs])

        f = gaussian_kde(np.vstack([lonp, latp]), bw_method=KDE_BW)
        f_values = f.evaluate(positions).reshape(kde.shape)
        kde = 5/np.max(f_values) * (1 - self.mask) * f_values * (h>0) + kde
        print('Computed new KDE')

        self.binX = binX
        self.binY = binY

        return kde

    def _get_bins(self, lon, lat, xEdges, yEdges):
        binX = np.zeros(len(lon), dtype='int')
        binY = np.zeros(len(lat), dtype='int')

        for i in range(len(lon)):
            for j in range(len(xEdges)-1):
                if (lon[i] >= xEdges[j]) and (lon[i] <= xEdges[j+1]):
                    binX[i] = j
                    break

        for i in range(len(lat)):
            for j in range(len(yEdges)-1):
                if (lat[i] >= yEdges[j]) and (lat[i] <= yEdges[j+1]):
                    binY[i] = j
                    break

        return binX, binY
    
    def robot_feedback(self, robot_id, xgrid, ygrid, robot_heading, lon=None, lat=None):

        print('[ROBOT_FB] Robot ' + str(robot_id) + ' is at ' + str(xgrid) + ', ' + str(ygrid))

        # Update robot position]
        self.robots_pos[robot_id, :] = [xgrid, ygrid]
        self.robots_heading[robot_id] = robot_heading
        
        # Consume existing particles
        particles_idx = self.idx[np.where(np.logical_and(self.binX == xgrid, self.binY == ygrid))[0]]
        self.lon = np.delete(self.lon, particles_idx)
        self.lat = np.delete(self.lat, particles_idx)

        # TODO Add sensed particles


        # Compute new global idx
        I1 = np.where(self.lon >= self.minLon)[0]
        lonI = self.lon[I1]
        latI = self.lat[I1]

        I2 = np.where(lonI <= self.maxLon)[0]
        lonI = lonI[I2]
        latI = latI[I2]

        I3 = np.where(latI >= self.minLat)[0]
        lonI = lonI[I3]
        latI = latI[I3]

        I4 = np.where(latI <= self.maxLat)[0]
        lonI = lonI[I4]
        latI = latI[I4]

        self.idx = I1[I2[I3[I4]]]

        # Compute kde
        self.kde = self._compute_kde(lonI, latI)


    def report_oil(self, lon, lat):
        self._gnome.add_oil(lon, lat)

    def get_kde(self):
        return self.kde

    def get_env_sensibility(self):
        return self.dist_grid

    def get_robots_pos(self):
        return self.robots_pos
    
    def get_robots_heading(self):
        return self.robots_heading

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

