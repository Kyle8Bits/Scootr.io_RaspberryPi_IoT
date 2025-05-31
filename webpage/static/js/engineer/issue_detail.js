function showFlash(message, type = "success") {
  const banner = document.getElementById("flash-banner");
  if (!banner) return;

  banner.className = `alert alert-${type}`;
  banner.textContent = message;
  banner.classList.remove("hidden");

  setTimeout(() => {
    banner.classList.add("hidden");
  }, 3000);
}
document.querySelector('form').addEventListener('submit', async function(e) {
  e.preventDefault();

  const formData = new FormData(this);
  
  try {
    const response = await fetch(this.action, {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();

    if (result.success) {
      showFlash(result.message, 'success');
    } else {
      showFlash(result.error || 'Failed to claim issue.', 'error');
    }
  } catch (err) {
    showFlash('An error occurred.', 'error');
    console.error(err);
  }
});
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