let map;
let heatmap;
let robots_markers, robots_drawn;
let region, polygon, region_drawn;
let isl_markers, isl_drawn;
let configured_mission;

var interval = setInterval(run, 3000); // 3 seconds repeat

function initMap() {

    map = new google.maps.Map($("#map")[0], {
        zoom: 10,
        center: { lat: -9.00, lng: -34.75 },
        mapTypeId: "roadmap",
    });

    // Particles
    $.getJSON({
        url: 'http://127.0.0.1:5000/simulation/particles/minLon:-35.3&maxLon:-34.9&minLat:-9.35&maxLat:-8.9',
        success: function(data) {

            heatmap = new google.maps.visualization.HeatmapLayer({
                data: getPoints(data.particles),
                map: map,
                radius: 20
            });

        }
    });

    // ISL
    $.getJSON({
        url: 'http://127.0.0.1:5000/simulation/isl',
        success: function(data) {

            var isl = data.isl;

            isl_markers = [];
            for (var i = 0; i < isl.length; i++) {
                isl_markers.push(new google.maps.Marker({
                    position: { lat: isl[i][1], lng: isl[i][0] },
                    map,
                    title: "ISL:  " + isl[i][2],
                }))
            }

            isl_drawn = true;

        }
    });

    // Checking if mission is configured
    if ($("#robots_button").length == 0) {
        configured_mission = false;
    } else {
        configured_mission = true;
    }

    if (configured_mission) {
        // Robots
        $.getJSON({
            url: 'http://127.0.0.1:5000/mission/robots_lon_lat',
            success: function(data) {

                var robots_lon_lat = data.robots_lon_lat;
                var robots_heading = data.robots_heading;

                robots_markers = [];
                for (var i = 0; i < robots_lon_lat.length; i++) {
                    robots_markers.push(new google.maps.Marker({
                        position: { lat: robots_lon_lat[i][1], lng: robots_lon_lat[i][0] },
                        map,
                        title: "Robot " + i + '; Lon:' + robots_lon_lat[i][0] + ', Lat: ' + robots_lon_lat[i][1] + ', H: ' + robots_heading[i],
                    }))
                }

                robots_drawn = true;

            }
        });

        // Region
        $.getJSON({
            url: 'http://127.0.0.1:5000/mission/region',
            success: function(data) {

                var coords = []
                var outerCoords = [];
                for (var i = 0; i < data.region.length; i++) {
                    outerCoords.push({ lat: data.region[i][1], lng: data.region[i][0] });
                }

                coords.push(outerCoords)

                if (data.innerRegions.length > 0) {
                    for (var i = 0; i < data.innerRegions.length; i++) {
                        var innerCoords = [];
                        for (var j = 0; j < data.innerRegions[i].length; j++) {
                            innerCoords.push({ lat: data.innerRegions[i][j][1], lng: data.innerRegions[i][j][0]})
                        }
                        coords.push(innerCoords)
                    }
                }
                
                polygon = new google.maps.Data.Polygon(coords);

                region = map.data.add({
                    geometry: polygon
                });

                region_drawn = true;
            }
        });
    }

}

function toggleParticles() {
    heatmap.setMap(heatmap.getMap() ? null : map);
}

function toggleRobots() {

    var obj = map;

    if (robots_drawn) {
        obj = null;
        robots_drawn = false;
    } else {
        robots_drawn = true;
    }

    for (var i = 0; i < robots_markers.length; i++) {
        robots_markers[i].setMap(obj);
    }
}

function toggleRegion() {
    if (region_drawn) {

        map.data.remove(region);
        region_drawn = false;

    } else {

        region = map.data.add({
            geometry: polygon
        });

        region_drawn = true;
    }
}


function toggleISL() {

    var obj = map;

    if (isl_drawn) {
        obj = null;
        isl_drawn = false;
    } else {
        isl_drawn = true;
    }

    for (var i = 0; i < isl_markers.length; i++) {
        isl_markers[i].setMap(obj);
    }
}

function getPoints(particles) {
    var latlng = [];

    for (var i = 0; i < particles[0].length; i++) {
        latlng.push(new google.maps.LatLng(particles[1][i], particles[0][i]));
    }

    return latlng;
}

function run() {
    // KDE
    $.getJSON({
        url: 'http://127.0.0.1:5000/simulation/particles/minLon:-35.3&maxLon:-34.9&minLat:-9.35&maxLat:-8.9',
        success: function(data) {

            particles_points = getPoints(data.particles);

            heatmap.setData(particles_points);

        }
    });

    if (configured_mission) {
        // Robots
        $.getJSON({
            url: 'http://127.0.0.1:5000/mission/robots_lon_lat',
            success: function(data) {

                var robots_lon_lat = data.robots_lon_lat;
                var robots_heading = data.robots_heading;

                for (var i = 0; i < robots_markers.length; i++) {
                    robots_markers[i].setPosition({ lat: robots_lon_lat[i][1], lng: robots_lon_lat[i][0] });
                    robots_markers[i].setTitle('Robot ' + i + '; Lon:' + robots_lon_lat[i][0] + ', Lat: ' + robots_lon_lat[i][1] + ', H: ' + robots_heading[i])
                }

            }
        });
    }
}