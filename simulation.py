from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta

from scipy.stats import gaussian_kde

import numpy as np
from fastkml import kml
from shapely import geometry

KDE_BW = 0.2        # KDE Bandwidth
RES_GRID = 111.0    # Grid resolution (km in each cell)

class Simulation(object):
    def __init__(self, interval, region):

        self._timer     = None
        self.interval   = interval
        self.is_running = False
        self.start()
        
        # Instance for gnome interface
        self._gnome = GnomeInterface()

        # Read kml and extract coordinates
        with open(region) as regionFile:
            regionString = regionFile.read()

        regionKML = kml.KML()
        regionKML.from_string(regionString)
        regionPolygon = list(list(list(regionKML.features())[0].features())[0].features())[0].geometry
        (minLon, minLat, maxLon, maxLat) = regionPolygon.bounds
        coords = np.array(regionPolygon.exterior.coords)

        # Create grid maps based on region boundaries
        self.width = int(np.ceil(RES_GRID * (maxLon - minLon)))
        self.height = int(np.ceil(RES_GRID * (maxLat - minLat)))
        
        self.mask = np.zeros((self.height, self.width))
        self.dist_grid = np.zeros((self.height, self.width))

        for i in range(self.width):
            for j in range(self.height):
                if regionPolygon.intersects(geometry.Point((i/RES_GRID) + minLon, (j/RES_GRID) + minLat)) == False:
                    self.mask[j, i] = 1
                else:
                    #self.dist_grid(j, i) = RES_GRID * 
                    pass
        
        self.mask_idx = np.argwhere(self.mask.T == 0) # indexes of cells inside polygon

        #self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)
        lon, lat = self._gnome.get_particles()
        self.kde = self._compute_kde(lon, lat)
        #max_dist=max(max(self.dist_grid))
        #self.dist_grid = 1/max_dist*5*(~self.mask.*max_dist-self.dist_grid)+self._kde

    def _run(self):
        self.is_running = False
        self.start()
        
        # Cyclic code here
        self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)
        lon, lat = self._gnome.get_particles()
        self._kde = self._compute_kde()

    def _compute_kde(self, lon=None, lat=None):
        kde = -1 * self.mask # No Fly Zones cells are -1 valued

        if (lon is not None) and (lat is not None):
            h, yEdges, xEdges = np.histogram2d(lat, lon, bins=[self.height, self.width])

            xls = np.mean(np.array([xEdges[1:-2], xEdges[2:-1]]), axis=0)
            yls = np.mean(np.array([yEdges[1:-2], yEdges[2:-1]]), axis=0)
            xx, yy = np.meshgrid(xls, yls)

            positions = np.vstack([xx.T.ravel(), yy.T.ravel()]).T

            binX, binY = self._get_bins(lon, lat, xEdges, yEdges)

            lonp = np.array([], dtype='float64')
            latp = np.array([], dtype='float64')

            for i in range(self.mask_idx.shape[0]):
                idxs = np.where((binX == self.mask_idx[i, 0]) and (binY == self.mask_idx[i, 1]))
                lonp = np.append(lonp, lon[idxs])
                latp = np.append(latp, lat[idxs])

            f = gaussian_kde(np.vstack([lonp.T, latp.T]).T, bw_method=KDE_BW)
            f_values = f.evaluate(positions).reshape(self.kde.shape)
            kde = 5/np.max(f) * (1 - mask) * f * (h>0) + kde

        return kde

    def _get_bins(self, lon, lat, xEdges, yEdges):
        binX = np.zeros(len(lon))
        binY = np.zeros(len(lat))

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
    
    def robot_feedback(self, xgrid, ygrid, lon, lat):
        pass # remove

    def get_kde(self):
        return self.kde

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

