//https://leafletjs.com/examples/quick-start/
//https://github.com/mathiasleroy/Belgium-Geographic-Data/blob/master/dist/polygons/geojson/Belgium.provinces.WGS84.geojson?short_path=2e1fca2
//https://openstreetmap.be/en/projects/howto/leaflet.html
var map = L.map("map").setView([50.7, 4.5], 7);

function getToken(){
    var val = "; " + document.cookie;
    var parts = val.split("; csrftoken=");
    if (parts.length === 2){
        return parts.pop().split(";").shift()
    }
}

var options = {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getToken()
    }
}

function getFarmers(){
    fetch("/accounts/farmers/", options)
    .then(response => {
        if (!response.ok){
            throw new Error("Not OK");
        }
        return response.json();
    })
    .then(data => {
        var farmers = data.farmers;
        var location = data.location;
        var longitude = location[0];
        var latitude = location[1];
        var farmIcon = L.icon({
            iconUrl: "/media/icon/marker.png",
            iconSize: [50, 50],
            iconAnchor: [10, 30],
            popupAnchor: [15, -30]
        });
        farmers.forEach(farmer => {
            if (farmer.latitude !== null && farmer.longitude !== null && farmer.latitude !== latitude && farmer.longitude !== longitude){
                var marker = L.marker([farmer.latitude, farmer.longitude], { icon: farmIcon }).addTo(map);
                var url = "<a href=../../accounts/user/"+ farmer.pk + ">" + farmer.username + "</a>"
                marker.bindPopup(url);
            }
        });
        if (latitude !== null && longitude !== null){
            L.marker([latitude, longitude]).addTo(map);
        }
    })
    .catch(error => console.error(error.message));
}


L.tileLayer('https://tile.openstreetmap.be/osmbe/{z}/{x}/{y}.png', {
    attribution:
        '&copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors' +
        ', Tiles courtesy of <a href="https://geo6.be/">GEO-6</a>',
    maxZoom: 18
}).addTo(map);

fetch("/static/farmfresh/js/belgium.geojson")
.then(response => response.json())
.then(data => {
    return fetch("/static/farmfresh/js/crop_data.json")
    .then(response => response.json())
    .then(cropData => {
        var belgiumLayer = L.geoJSON(data, {
            style: function(feature){
                var areaName = feature.properties.NameENG
                var crops = cropData.areas[areaName]
                var areaColor = "#ffffff"
                var cropColor = {
                    "Apples": "red",
                    "Pears": "#91d147",
                    "Berries": "purple",
                    "Chicory": "yellow",
                    "Brussels Sprouts": "#305726",
                    "Leeks": "30c526",
                    "Potatoes": "#ffda26",
                    "Strawberries": "#ff004a",
                    "Sugar Beets": "#ffffb6",
                    "Asparagus": "#003100"
                }
                if (crops.length > 0){
                    areaColor = cropColor[crops[0]];
                }
                else areaColor = "gray"

                return{
                    color: areaColor,
                    weight: 2,
                    fillColor: areaColor,
                    fillOpacity: 0.5
                };
            },
            onEachFeature: function(feature, layer){
                var areaName = feature.properties.NameENG;
                var crops = cropData.areas[areaName];
                var text = "<b>" + areaName + "</b><br><br><b>Speciality:</b><br>";
                if (crops.length > 0){
                    text += crops.join("<br>");
                }
                else {
                    text += "No specific crop";
                }
                layer.bindPopup(text);
            }
        }).addTo(map);
    });
});

document.addEventListener("DOMContentLoaded", getFarmers);