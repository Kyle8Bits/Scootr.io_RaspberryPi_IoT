let issues = [];
let currentPage = 1;
const itemsPerPage = 10;
let pendingResolveIssueId = null;

window.onload = () => {
  fetchEngineerIssues();
  setupResolutionTypeButtons();
};

// Fetch issues assigned to the engineer
function fetchEngineerIssues() {
  fetch("/engineer/issues/api")
    .then(res => res.json())
    .then(data => {
      if (Array.isArray(data)) {
        issues = data;
        currentPage = 1;
        renderIssues();
      } else {
        console.error("❌ Error loading issues:", data.error);
      }
    })
    .catch(err => {
      console.error("❌ Failed to fetch engineer issues:", err);
    });
}

// Render issues into table
function renderIssues() {
  const tbody = document.getElementById("issues-body");
  tbody.innerHTML = "";

  const statusFilter = document.getElementById("status-filter").value;
  const filtered = issues.filter(issue =>
    statusFilter === "all" || issue.status.toLowerCase() === statusFilter.toLowerCase()
  );

  const start = (currentPage - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  const paginated = filtered.slice(start, end);

  paginated.forEach(issue => {
    const row = document.createElement("tr");
    const hasMap = issue.latitude && issue.longitude;
    const resolvedDisplay = issue.resolved_at === "None" || !issue.resolved_at ? "-" : formatDate(issue.resolved_at);

    row.innerHTML = `
      <td>${issue.id}</td>
      <td>${issue.scooter_id}</td>
      <td>${issue.customer_id}</td>
      <td>${issue.issue_type}</td>
      <td>${issue.additional_details || "-"}</td>
      <td>${formatDate(issue.reported_at)}</td>
      <td>${issue.status}</td>
      <td>${formatDate(issue.approved_at)}</td>
      <td>${resolvedDisplay}</td>
      <td>
        ${hasMap
          ? `<a class="btn-map" onclick="getDirections(${ issue.latitude }, ${ issue.longitude })" target="_blank">📍 Map</a>`
          : `<span class="disabled-action">No Location</span>`}
        
      </td>
      <td>
        ${
          issue.status === "Approved"
            ? `<button class="btn-submit" onclick="confirmResolve(${issue.id})">Resolve</button>`
            : `<span class="resolved-box">Resolved</span>`
        }
        <button class="btn-view" onclick="viewScooterDetails(${issue.scooter_id})">View Scooter</button>

      </td>

    `;
    tbody.appendChild(row);
  });

  updatePagination(filtered.length);
}
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
// Format date string
function formatDate(str) {
  if (!str || str === "None" || str === "null") return "-";
  const d = new Date(str);
  return isNaN(d) ? "-" : d.toLocaleString();
}

// Pagination
function updatePagination(totalItems) {
  const pageInfo = document.getElementById("page-info");
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  document.getElementById("prev-page").disabled = currentPage === 1;
  document.getElementById("next-page").disabled = currentPage === totalPages;
}

document.getElementById("prev-page").addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderIssues();
  }
});

document.getElementById("next-page").addEventListener("click", () => {
  const totalPages = Math.ceil(issues.length / itemsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderIssues();
  }
});

function filterIssuesByStatus() {
  currentPage = 1;
  renderIssues();
}

// Open modal
function confirmResolve(issueId) {
  pendingResolveIssueId = issueId;
  document.getElementById("resolve-modal").classList.remove("hidden");

  // Clear previous selection
  document.querySelectorAll(".pill-option").forEach(btn => btn.classList.remove("active"));
  document.getElementById("resolution-type").value = "";
  document.getElementById("resolution-details").value = "";
}

// Close modal
function closeResolveModal() {
  document.getElementById("resolve-modal").classList.add("hidden");
  pendingResolveIssueId = null;
}

// Select resolution type from pills
function setupResolutionTypeButtons() {
  document.querySelectorAll(".pill-option").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pill-option").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("resolution-type").value = btn.dataset.value;
    });
  });
}

// Submit resolution
document.getElementById("confirm-resolve-btn").addEventListener("click", () => {
  const resolutionType = document.getElementById("resolution-type").value;
  const resolutionDetails = document.getElementById("resolution-details").value.trim();

  if (!resolutionType) {
    alert("Please select a resolution type.");
    return;
  }

  if (!resolutionDetails) {
    alert("Please provide resolution details.");
    return;
  }

  fetch(`/engineer/issues/${pendingResolveIssueId}/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      resolution_type: resolutionType,
      resolution_details: resolutionDetails
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        fetchEngineerIssues();
        showFlash("✅ Issue marked as resolved.", "success");
      } else {
        showFlash("❌ Failed to resolve issue.", "error");
      }
    })
    .catch(err => {
      console.error("❌ Error resolving issue:", err);
      showFlash("❌ Error resolving issue.", "error");
    })
    .finally(() => {
      closeResolveModal();
    });
});

// Flash banner utility
function showFlash(message, type = "success") {
  const banner = document.getElementById("flash-banner");
  if (!banner) return;

  banner.textContent = message;
  banner.className = type === "success" ? "alert alert-success" : "alert alert-error";
  banner.classList.remove("hidden");

  setTimeout(() => banner.classList.add("hidden"), 4000);
}

// View Scooter Info
function viewScooterDetails(scooterId) {
  fetch(`/engineer/scooter/${scooterId}`)
    .then(res => res.json())
    .then(data => {
      const c = document.getElementById("scooter-details");
      c.innerHTML = `
        <p><strong>ID:</strong> ${data.id}</p>
        <p><strong>Make:</strong> ${data.make}</p>
        <p><strong>Color:</strong> ${data.color}</p>
        <p><strong>Zone:</strong> ${data.zone_id}</p>
        <p><strong>Power Remaining:</strong> ${data.power_remaining}%</p>
        <p><strong>Cost / min:</strong> $${parseFloat(data.cost_per_minute).toFixed(2)}</p>
        <img src="${data.image_url}" alt="Scooter Image" style="max-width:100%; margin-top:1rem; border-radius:8px;" />
      `;
      document.getElementById("scooter-modal").classList.remove("hidden");
    })
    .catch(err => {
      console.error("❌ Failed to fetch scooter:", err);
      alert("Unable to load scooter info.");
    });
}

function closeScooterModal() {
  document.getElementById("scooter-modal").classList.add("hidden");
}
