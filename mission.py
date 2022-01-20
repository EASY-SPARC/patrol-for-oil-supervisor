from scipy.stats import gaussian_kde

import numpy as np
from fastkml import kml
from shapely import geometry
import shapefile

KDE_BW = 0.2        # KDE Bandwidth
RES_GRID = 111.0    # Grid resolution (km in each cell)

class Mission(object):
    def __init__(self, t_mission, robots, region, simulation, env_sensitivity_mode):
        self.simulation = simulation
        self.res_grid = RES_GRID
        self.robots = robots
        self.env_sensitvity_mode = env_sensitivity_mode

        # Read shape file
        shpfile = shapefile.Reader('./assets/shp/BRA_admin_AL.shp')
        feature = shpfile.shapeRecords()[0]
        first = feature.shape.__geo_interface__
        shp = geometry.shape(first)
        al_coords = np.array(shp.geoms[3].exterior.coords)

        # Read kml and extract coordinates
        with open(region, 'rb') as regionFile:
            regionString = regionFile.read()

        # print(regionString)
        regionKML = kml.KML()
        regionKML.from_string(regionString)
        placemarks = list(list(list(regionKML.features())[0].features())[0].features())
        regionPolygon = placemarks[0].geometry
        (self.minLon, self.minLat, self.maxLon, self.maxLat) = regionPolygon.bounds
        self.coords = np.array(regionPolygon.exterior.coords)

        # It may have inner cutoff polygons
        innerPoly = []
        self.innerPolyCoords = []
        for i in range(1, len(placemarks)):
            innerPoly.append(placemarks[i].geometry)
            self.innerPolyCoords.append(np.array(placemarks[i].geometry.exterior.coords).tolist())
        
        # Create grid maps based on region boundaries
        self.width = int(np.ceil(RES_GRID * (self.maxLon - self.minLon)))
        self.height = int(np.ceil(RES_GRID * (self.maxLat - self.minLat)))
        
        self.mask = np.zeros((self.height, self.width))
        self.dist_grid = np.zeros((self.height, self.width))

        # Checking which cells are inside the region of interest polygon and calculating distance to nearest point in coast
        for i in range(self.width):
            for j in range(self.height):
                point_lon = (i/RES_GRID) + self.minLon
                point_lat = (j/RES_GRID) + self.minLat
                # Checking if point is outside permitted fly zone
                # print(str(point_lon) + ', ' + str(point_lat) + ' -> ' + str(regionPolygon.intersects(geometry.Point(point_lon, point_lat))))
                fly_zone_flag = True
                if regionPolygon.intersects(geometry.Point(point_lon, point_lat)) == False:
                    fly_zone_flag = False
                else:
                    for k in range(len(innerPoly)):
                        if innerPoly[k].intersects(geometry.Point(point_lon, point_lat)) == True:
                            fly_zone_flag = False
                            break

                if fly_zone_flag == True:
                    dist = np.sqrt((point_lon - al_coords[:, 0])**2 + (point_lat - al_coords[:, 1])**2)
                    self.dist_grid[j, i] = RES_GRID * np.min(dist)
                else:
                    self.mask[j, i] = 1
      
        self.mask_idx = np.argwhere(self.mask.T == 0) # indexes of cells inside polygon

        # Normalizing Environmental Sensibility and applying region of interest mask
        max_dist = np.max(self.dist_grid)
        self.dist_grid = 1/max_dist * 5 * ((1 - self.mask) * max_dist - self.dist_grid) - self.mask
        
        # Filtering particles to square domain and saving its indexes for later use
        I1 = np.where(self.simulation.lon >= self.minLon)[0]
        lonI = simulation.lon[I1]
        latI = simulation.lat[I1]

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

        self.potential_field = self._compute_isl_pot_field(simulation.isl)

        # Initializing robots positions in grid map
        found_flag = False
        start_pos_x = 0
        start_pos_y = 0
        for i in range(self.width):            
            for j in range(0, int(np.floor(self.height/2))):
                if self.mask[int(self.height/2) + j, i] == 0:
                    found_flag = True
                    start_pos_x = i
                    start_pos_y = int(self.height/2) + j
                    break
                elif self.mask[int(self.height/2) - j, i] == 0:
                    found_flag = True
                    start_pos_x = i
                    start_pos_y = int(self.height/2) - j
                    break
            if found_flag == True:
                break
        
        for robot in self.robots:
            robot['pos_x'] = start_pos_x
            robot['pos_y'] = start_pos_y

    def _compute_kde(self, lon, lat):
        print('Computing new KDE')
        kde = -1 * self.mask # No Fly Zones cells are -1 valued
    
        h, yEdges, xEdges = np.histogram2d(x=lat, y=lon, bins=[self.height, self.width])

        xls = np.mean(np.array([xEdges[0:-1], xEdges[1:]]), axis=0)
        yls = np.mean(np.array([yEdges[0:-1], yEdges[1:]]), axis=0)
        xx, yy = np.meshgrid(xls, yls)

        positions = np.vstack([xx.ravel(), yy.ravel()])

        binX, binY = self._get_bins(lon, lat, xEdges, yEdges)

        lonp = np.array([], dtype='float64')
        latp = np.array([], dtype='float64')

        # Find which particles are inside the polygon
        for i in range(self.mask_idx.shape[0]):
            idxs = np.where(np.logical_and(binX == self.mask_idx[i, 0], binY == self.mask_idx[i, 1]))[0]
            lonp = np.append(lonp, lon[idxs])
            latp = np.append(latp, lat[idxs])

        if len(lonp) != 0:
            f = gaussian_kde(np.vstack([lonp, latp]), bw_method=KDE_BW)
            f_values = f.evaluate(positions).reshape(kde.shape)
            kde = 5/np.max(f_values) * (1 - self.mask) * f_values * (h>0) + kde
        else:
            kde = -self.mask
        print('Computed new KDE')

        self.binX = binX
        self.binY = binY

        return kde

    def _compute_isl_pot_field(self, isl):
        # Filtering ISL
        idx = np.where(isl[:, 1] >= self.minLat - 1)[0]
        isl_filtered = isl[idx, :]

        idx = np.where(isl_filtered[:, 1] <= self.maxLat + 1)[0]
        isl_filtered = isl_filtered[idx, :]

        # Gaussians ISL-centered as potential fields
        sigma = 0.1
        potential_field = np.zeros((self.height, self.width))
        for potential in isl_filtered:
            for i in range(self.width):
                for j in range(self.height):
                    curr_lon = (i/RES_GRID) + self.minLon
                    curr_lat = (j/RES_GRID) + self.minLat

                    lon_0 = potential[0]
                    lat_0 = potential[1]
                    Amp = potential[2]

                    potential_field[j, i] += Amp * np.exp(-( \
                        ((curr_lon - lon_0)**2)/(2 * sigma**2) + \
                            ((curr_lat - lat_0)**2)/(2 * sigma**2) \
                                ))
        
        max_potential = np.max(potential_field)
        potential_field = 1/max_potential * 5 * (1 - self.mask) * potential_field - self.mask

        return potential_field

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
        try:
            robot = next(robot for robot in self.robots if robot["id"] == robot_id)
            robot['pos_x'] = xgrid
            robot['pos_y'] = ygrid
            robot['heading'] = robot_heading
        except StopIteration:
            print('[ROBOT_FB] No robot with id ' + robot_id)
            return
        
        # Consume existing particles
        particles_idx = self.idx[np.where(np.logical_and(self.binX == xgrid, self.binY == ygrid))[0]]
        self.simulation.lon = np.delete(self.simulation.lon, particles_idx)
        self.simulation.lat = np.delete(self.simulation.lat, particles_idx)

        # Compute new global idx
        I1 = np.where(self.simulation.lon >= self.minLon)[0]
        lonI = self.simulation.lon[I1]
        latI = self.simulation.lat[I1]

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

    def get_kde(self):
        return self.kde
    
    def get_robots_pos(self):
        robots_pos = np.array([[robot['pos_x'], robot['pos_y']] for robot in self.robots])
        return robots_pos

    def get_robots_lon_lat(self):
        robots_lon_lat = np.copy(self.get_robots_pos()).astype('float')

        robots_lon_lat[:, 0] = (robots_lon_lat[:, 0]/RES_GRID) + self.minLon
        robots_lon_lat[:, 1] = (robots_lon_lat[:, 1]/RES_GRID) + self.minLat

        return robots_lon_lat
         
    def get_robots_heading(self):
        robots_heading = np.array([robot['heading'] for robot in self.robots])
        return robots_heading

    def get_region(self):
        return self.coords, self.innerPolyCoords

    def get_robots_weights(self):
        robots_weights = np.array([[robot['kappa'], robot['omega_c'], robot['omega_s'], robot['omega_d'], robot['omega_n']] for robot in self.robots])
        return robots_weights

    def get_env_sensibility(self):
        if self.env_sensitvity_mode == 0:
            return self.potential_field
        else:
            return self.dist_grid