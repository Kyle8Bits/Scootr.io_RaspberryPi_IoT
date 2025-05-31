let reportData = [];
let currentPage = 1;
const itemsPerPage = 10;

window.onload = () => {
  fetchResolvedIssues();
};

// Fetch resolved issues from API
function fetchResolvedIssues() {
  fetch("/engineer/report/api")
    .then(res => res.json())
    .then(data => {
      if (Array.isArray(data)) {
        reportData = data;
        currentPage = 1;
        renderReport();
      } else {
        showFlash("❌ Failed to load reports.");
      }
    })
    .catch(err => {
      console.error("Fetch error:", err);
      showFlash("❌ Server error.");
    });
}

// Render the table
function renderReport() {
    const tbody = document.getElementById("report-body");
    tbody.innerHTML = "";
  
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const pageItems = reportData.slice(start, end);
  
    pageItems.forEach(item => {
      console.log("🧪 approved_at:", item.approved_at, "| resolved_at:", item.resolved_at);
  
      const resolutionTime = calculateTimeDiff(item.approved_at, item.resolved_at);
      const row = document.createElement("tr");
  
      row.innerHTML = `
        <td>${item.issue_id}</td>
        <td>${item.scooter_id}</td>
        <td>${item.issue_type}</td>
        <td>${formatDate(item.resolved_at)}</td>
        <td>${resolutionTime || "-"}</td>
        <td>${prettify(item.resolution_type)}</td>
        <td>${item.resolution_details}</td>
        <td>
          <button class="btn-view" onclick="viewScooterDetails(${item.scooter_id})">View Bike</button>
        </td>
      `;
      tbody.appendChild(row);
    });
  
    updatePagination(reportData.length);
  }
  

// Format date
function formatDate(str) {
  if (!str) return "-";
  const d = new Date(str);
  return isNaN(d) ? "-" : d.toLocaleString();
}

// Prettify resolution type
function prettify(slug) {
  return slug ? slug.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) : "-";
}

// Calculate time diff (hh:mm format)
function calculateTimeDiff(start, end) {
    if (!start || !end) return "-";
  
    const startTime = new Date(start);
    const endTime = new Date(end);
    let diffMs = endTime - startTime;
  
    // ✅ If negative, flip it so we still get a readable duration
    const isNegative = diffMs < 0;
    diffMs = Math.abs(diffMs);
  
    const minutes = Math.floor(diffMs / 60000);
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
  
    return isNegative
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h ${remainingMinutes}m`;
  }
  

// Pagination
function updatePagination(totalItems) {
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  document.getElementById("page-info").textContent = `Page ${currentPage} of ${totalPages}`;
  document.getElementById("prev-page").disabled = currentPage === 1;
  document.getElementById("next-page").disabled = currentPage === totalPages;
}

document.getElementById("prev-page").addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderReport();
  }
});

document.getElementById("next-page").addEventListener("click", () => {
  const totalPages = Math.ceil(reportData.length / itemsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderReport();
  }
});

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
        <img src="${data.image_url}" alt="Scooter Image" style="max-width:100%; border-radius: 8px; margin-top: 1rem;" />
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

// Flash messages
function showFlash(message, type = "error") {
  const banner = document.getElementById("flash-banner");
  if (!banner) return;

  banner.textContent = message;
  banner.className = type === "success" ? "alert alert-success" : "alert alert-error";
  banner.classList.remove("hidden");

  setTimeout(() => banner.classList.add("hidden"), 4000);
}

// Export as CSV
function downloadCSV() {
  if (reportData.length === 0) {
    showFlash("No data to export.");
    return;
  }

  const headers = [
    "Issue ID",
    "Scooter ID",
    "Issue Type",
    "Resolved At",
    "Resolution Time",
    "Resolution Type",
    "Details"
  ];

  const rows = reportData.map(item => {
    const resolvedTime = formatDate(item.resolved_at);
    const diff = calculateTimeDiff(item.approved_at, item.resolved_at);
    return [
      item.issue_id,
      item.scooter_id,
      item.issue_type,
      resolvedTime,
      diff,
      prettify(item.resolution_type),
      `"${item.resolution_details.replace(/"/g, '""')}"`
    ];
  });

  const csvContent =
    [headers.join(","), ...rows.map(r => r.join(","))].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "engineer_resolved_issues.csv";
  link.click();
  URL.revokeObjectURL(url);
}
