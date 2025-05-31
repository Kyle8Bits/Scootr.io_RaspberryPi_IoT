// async function initMap() {
//   const mapIconUrl = document.getElementById("map").dataset.icon;
//   const position = { lat: 10.762622, lng: 106.660172 };

//   const { Map } = await google.maps.importLibrary("maps");
//   const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

//   const map = new Map(document.getElementById("map"), {
//     zoom: 14,
//     center: position,
//     mapId: "4419df00caf07abd",
//   });

//   const iconImg = document.createElement("img");
//   iconImg.src = mapIconUrl;
//   iconImg.style.width = "40px";
//   iconImg.style.height = "40px";

//   new AdvancedMarkerElement({
//     map: map,
//     position: position,
//     content: iconImg,
//     title: "Engineer Location",
//   });
// }

// async function initMap() {
//   const { Map } = await google.maps.importLibrary("maps");
//   const map = new Map(document.getElementById("map"), {
//     zoom: 14,
//     center: { lat: 10.762622, lng: 106.660172 }
//   });
// }
// document.addEventListener("DOMContentLoaded", function () {
//   if (typeof google !== 'undefined') {
//     initMap();
//   }
// });
// window.initMap = initMap;

function getDirections(destLat, destLng) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
      const userLat = position.coords.latitude;
      const userLng = position.coords.longitude;

      const directionsUrl = `https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLng}&destination=${destLat},${destLng}&travelmode=walking`;
      window.open(directionsUrl, '_blank');
    }, (err) => {
      alert("Failed to get current location. Please enable GPS.");
    });
  } else {
    alert("Geolocation is not supported by this browser.");
  }
}