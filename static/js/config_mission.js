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

function addRobots() {
    var i = parseInt($("#n_robots_input").val()) + 1
    $("#n_robots_input").val(i);

    $('#robots_table > tbody:last-child').append(`<tr id="robot` + i + `">
    <td>` + i + `</td>
    <td><input value="0" class="form-control" name="kappa_` + i + `"></td>
    <td><input value="0" class="form-control" name="omega_c` + i + `"></td>
    <td><input value="0" class="form-control" name="omega_s` + i + `"></td>
    <td><input value="0" class="form-control" name="omega_d` + i + `"></td>
    <td><input value="0" class="form-control" name="omega_n` + i + `"></td>
    </tr>`);

    if (i > 0) {
        $("#save").attr("disabled", false);
    }
}

function subtractRobots() {
    var new_value = parseInt($("#n_robots_input").val()) - 1;
    if (new_value > 0) {
        $("#n_robots_input").val(parseInt($("#n_robots_input").val()) - 1);

        $('#robots_table > tbody:last-child > tr:last').remove();
    }
}