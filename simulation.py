from threading import Timer
from gnome_interface import GnomeInterface
from datetime import datetime, timedelta
import numpy

class Simulation(object):
    def __init__(self, interval, region, res_grid):
        self._timer     = None
        self.interval   = interval
        self.is_running = False
        self.start()

        self._gnome = GnomeInterface()

        self.width = numpy.ceil(res_grid * ())

        self._kde = numpy.zeros((self.height, self.width))

    def _run(self):
        self.is_running = False
        self.start()
        
        # Cyclic code here
        [lon, lat] = self._gnome.step(datetime(2020, 9, 15, 12, 0, 0), False)
        self._kde = self._compute_kde(lon, lat)

    def _compute_kde(self, lon, lat):
        kde = numpy.zeros((self.height, self.width))
        return kde
    
    def robot_feedback(self, xgrid, ygrid, lon, lat):
        pass

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
