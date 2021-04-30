let map_simulation;
let vertices;
let valid;

function initMap() {

    map_simulation = new google.maps.Map($("#map_simulation")[0], {
        zoom: 7,
        center: { lat: -9.5, lng: -35.5 },
        mapTypeId: "roadmap",
    });

    var north = parseFloat($("#maxLat_input").val());
    var south = parseFloat($("#minLat_input").val());
    var east = parseFloat($("#maxLon_input").val());
    var west = parseFloat($("#minLon_input").val());

    const coords = [
        { lat: north, lng: west },
        { lat: north, lng: east },
        { lat: south, lng: east },
        { lat: south, lng: west },
        { lat: north, lng: west }
    ];

    const polygon = new google.maps.Polygon({
        paths: coords,
        strokeColor: "#FF0000",
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: "#FF0000",
        fillOpacity: 0.35,
    });

    vertices = polygon.getPath();

    polygon.setMap(map_simulation);
}

function updatePolygon() {
    vertices.clear();

    var north = parseFloat($("#maxLat_input").val());
    var south = parseFloat($("#minLat_input").val());
    var east = parseFloat($("#maxLon_input").val());
    var west = parseFloat($("#minLon_input").val());

    if ((north <= south) || (east <= west)) {
        $("#start").attr("disabled", true);
        $("#invalid").css("visibility", "visible");
    } else {
        vertices.push(new google.maps.LatLng({ lat: north, lng: west }));
        vertices.push(new google.maps.LatLng({ lat: north, lng: east }));
        vertices.push(new google.maps.LatLng({ lat: south, lng: east }));
        vertices.push(new google.maps.LatLng({ lat: south, lng: west }));
        vertices.push(new google.maps.LatLng({ lat: north, lng: west }));
        $("#start").attr("disabled", false);
        $("#invalid").css("visibility", "hidden");
    }
}