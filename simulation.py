from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta

import numpy as np
from fastkml import kml
from shapely import geometry

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
        self.width = int(np.ceil(res_grid * (maxLon - minLon)))
        self.height = int(np.ceil(res_grid * (maxLat - minLat)))
        
        self.mask = np.zeros((self.height, self.width))
        self.dist_grid = np.zeros((self.height, self.width))

        for i in range(self.width):
            for j in range(self.height):
                if regionPolygon.intersects(geometry.Point((i/res_grid) + minLon, (j/res_grid) + minLat)) == False:
                    self.mask[j, i] = 1
                else:
                    #self.dist_grid(j, i) = res_grid * 
                    pass
        
        self.kde = self._compute_kde()
        #max_dist=max(max(self.dist_grid))
        #self.dist_grid = 1/max_dist*5*(~self.mask.*max_dist-self.dist_grid)+self._kde


    def _run(self):
        self.is_running = False
        self.start()
        
        # Cyclic code here
        #[lon, lat] = self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)
        #self._kde = self._compute_kde(lon, lat)

    def _compute_kde(self, lon=None, lat=None):
        kde = -1 * self.mask # No Fly Zones cells are -1 valued

        if (lon is not None) and (lat is not None):
            # h = ...
            # f = ...
            #kde = 5/np.max(f) * np.logical_not(mask) * f * (h>0) + kde;
            pass # remove


        return kde
    
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

