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
        (self.minLon, self.minLat, self.maxLon, self.maxLat) = regionPolygon.bounds
        coords = np.array(regionPolygon.exterior.coords)

        # Create grid maps based on region boundaries
        self.width = int(np.ceil(RES_GRID * (self.maxLon - self.minLon)))
        self.height = int(np.ceil(RES_GRID * (self.maxLat - self.minLat)))
        
        self.mask = np.zeros((self.height, self.width))
        self.dist_grid = np.zeros((self.height, self.width))

        for i in range(self.width):
            for j in range(self.height):
                if regionPolygon.intersects(geometry.Point((i/RES_GRID) + self.minLon, (j/RES_GRID) + self.minLat)) == False:
                    self.mask[j, i] = 1
                else:
                    #self.dist_grid(j, i) = RES_GRID * 
                    pass
        
        self.mask_idx = np.argwhere(self.mask.T == 0) # indexes of cells inside polygon
        self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)

        lon, lat = self._gnome.get_particles()

        I1 = np.where(lon >= self.minLon)
        lonI = lon[I1]
        latI = lat[I1]

        I2 = np.where(lonI <= self.maxLon)
        lonI = lonI[I2]
        latI = latI[I2]

        I3 = np.where(latI >= self.minLat)
        lonI = lonI[I3]
        latI = latI[I3]

        I4 = np.where(latI <= self.maxLat)
        lonI = lonI[I4]
        latI = latI[I4]

        self.kde = self._compute_kde(lonI, latI)

        #max_dist=max(max(self.dist_grid))
        #self.dist_grid = 1/max_dist*5*(~self.mask.*max_dist-self.dist_grid)+self._kde

    def _run(self):
        self.is_running = False
        self.start()
        
        # Cyclic code here
        self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)

        lon, lat = self._gnome.get_particles()

        I1 = np.where(lon >= self.minLon)
        lonI = lon[I1]
        latI = lat[I1]

        I2 = np.where(lonI <= self.maxLon)
        lonI = lonI[I2]
        latI = latI[I2]

        I3 = np.where(latI >= self.minLat)
        lonI = lonI[I3]
        latI = latI[I3]

        I4 = np.where(latI <= self.maxLat)
        lonI = lonI[I4]
        latI = latI[I4]

        self.kde = self._compute_kde(lonI, latI)
        
    def _compute_kde(self, lon=None, lat=None):
        print('Computing new KDE')
        kde = -1 * self.mask # No Fly Zones cells are -1 valued

        if (lon is not None) and (lat is not None):
            h, yEdges, xEdges = np.histogram2d(x=lat, y=lon, bins=[self.height, self.width])

            xls = np.mean(np.array([xEdges[0:-1], xEdges[1:]]), axis=0)
            yls = np.mean(np.array([yEdges[0:-1], yEdges[1:]]), axis=0)
            xx, yy = np.meshgrid(xls, yls)

            #positions = np.vstack([xx.T.ravel(), yy.T.ravel()]).T
            positions = np.vstack([xx.ravel(), yy.ravel()])

            binX, binY = self._get_bins(lon, lat, xEdges, yEdges)

            lonp = np.array([], dtype='float64')
            latp = np.array([], dtype='float64')

            # Find which particles are inside the polygon (need optimization -- Too slow)
            for i in range(self.mask_idx.shape[0]):
                for j in range(len(binX)):
                    if (binX[j] == self.mask_idx[i, 0]) and (binY[j] == self.mask_idx[i, 1]):
                        lonp = np.append(lonp, lon[j])
                        latp = np.append(latp, lat[j])
                #idxs = np.where((binX == self.mask_idx[i, 0]) and (binY == self.mask_idx[i, 1]))
                #lonp = np.append(lonp, lon[idxs])
                #latp = np.append(latp, lat[idxs])

            f = gaussian_kde(np.vstack([lonp, latp]), bw_method=KDE_BW)
            f_values = f.evaluate(positions).reshape(kde.shape)
            kde = 5/np.max(f_values) * (1 - self.mask) * f_values * (h>0) + kde
            print('Computed new KDE')

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

