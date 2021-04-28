let map_simulation;
let map_mission;

function initMap() {

    map_simulation = new google.maps.Map($("#map_simulation")[0], {
        zoom: 10,
        center: { lat: -9.00, lng: -34.75 },
        mapTypeId: "roadmap",
    });

    map_mission = new google.maps.Map($("#map_mission")[0], {
        zoom: 10,
        center: { lat: -9.00, lng: -34.75 },
        mapTypeId: "roadmap",
    });

}