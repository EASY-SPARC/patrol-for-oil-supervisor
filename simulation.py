from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta

import numpy as np
from matplotlib import path
from fastkml import kml

def inpolygon(xq, yq, xv, yv):
    shape = xq.shape
    xq = xq.reshape(-1)
    yq = yq.reshape(-1)
    xv = xv.reshape(-1)
    yv = yv.reshape(-1)
    q = [(xq[i], yq[i]) for i in range(xq.shape[0])]
    p = path.Path([(xv[i], yv[i]) for i in range(xv.shape[0])])
    return p.contains_points(q).reshape(shape)

class Simulation(object):
    def __init__(self, interval, region, res_grid):
        self._timer     = None
        self.interval   = interval
        self.is_running = False
        self.start()
        
        res_grid = float(res_grid)

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
        self.width = np.ceil(res_grid * (maxLon - minLon))
        self.height = np.ceil(res_grid * (maxLat - minLat))
        
        self._mask = np.zeros((self.height, self.width))
        self._dist_grid = np.zeros((self.height, self.width))

        for i in range(self.width):
            for j in range(self.height):
                if inpolygon((i/res_grid) + minLon, (j/res_grid) + minLat, coords[:, 0], coords[:, 1]) == False:
                    self._mask(j, i) = 1
                else:
                    #self._dist_grid(j, i) = res_grid * 
                    pass
        
        self._kde = self._compute_kde()
        #max_dist=max(max(self._dist_grid))
        #self._dist_grid = 1/max_dist*5*(~self.mask.*max_dist-self._dist_grid)+self._kde


    def _run(self):
        self.is_running = False
        self.start()
        
        # Cyclic code here
        [lon, lat] = self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)
        self._kde = self._compute_kde(lon, lat)

    def _compute_kde(self, lon=None, lat=None):
        kde = np.NINF * self._mask # No Fly Zones cells are -inf valued
        kde = np.where(np.isnan(kde), 0, kde) # force numpy's -inf * 0 = 0, instead of nan

        if (lon is not None) and (lat is not None):
            # h = ...
            # f = ...
            #kde = 5/np.max(f) * np.logical_not(mask) * f * (h>0) + kde;
            pass # remove


        return kde
    
    def robot_feedback(self, xgrid, ygrid, lon, lat):
        pass # remove

    def get_kde():
        return self._kde

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

