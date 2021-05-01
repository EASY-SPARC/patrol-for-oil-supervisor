let map_simulation;
let vertices;
let valid;

function initMap() {

    map_mission = new google.maps.Map($("#map_mission")[0], {
        zoom: 7,
        center: { lat: -9.5, lng: -35.5 },
        mapTypeId: "roadmap",
    });

    var regionFile = $("#regionFile").val();

    const ctaLayer = new google.maps.KmlLayer({
        url: regionFile,
        map: map_mission,
    });
}