let issueReports = [];
let pendingResolveId = null;

// Fetch all issues on page load
function fetchIssueReports() {
  fetch("/admin/issues/api")
    .then(response => response.json())
    .then(data => {
      issueReports = Array.isArray(data) ? data : [];
      loadIssues();
    })
    .catch(err => {
      console.error("❌ Failed to load issue reports:", err);
    });
}

// Render issues into table
function loadIssues() {
  const tbody = document.getElementById("issue-body");
  tbody.innerHTML = "";

  const selectedStatus = document.getElementById("status-filter").value;

  issueReports
    .filter(report => selectedStatus === "all" || report.status.toLowerCase() === selectedStatus)
    .sort((a, b) => new Date(b.reported_at) - new Date(a.reported_at))
    .forEach(report => {
      const mapBtn = (report.latitude && report.longitude)
        ? `<a class="btn-map" href="https://maps.google.com/?q=${report.latitude},${report.longitude}" target="_blank">📍 Map</a>`
        : `<span class="disabled-action">No Location</span>`;

      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${report.id}</td>
        <td>${report.scooter_id}</td>
        <td>${report.customer_id}</td>
        <td>${report.issue_type}</td>
        <td>${report.additional_details}</td>
        <td>${formatDate(report.reported_at)}</td>
        <td>${report.status}</td>
        <td>${formatDate(report.updated_at)}</td>
        <td>
          ${report.status.toLowerCase() === "open"
            ? `<button class="btn-resolve" onclick="markAsResolved(${report.id})">✔️ Approve</button>`
            : `<span class="disabled-action">✅ Approved</span>`
          }
          <button class="btn-info" onclick="viewCustomer(${report.customer_id})">👤 View</button>
          ${mapBtn}
        </td>
      `;
      tbody.appendChild(row);
    });
}

// Filter dropdown handler
function filterByStatus() {
  loadIssues();
}

// Confirm approval modal trigger
function markAsResolved(issueId) {
  pendingResolveId = issueId;
  document.getElementById("resolve-modal").classList.remove("hidden");
}

// Approve the issue
document.getElementById("resolve-yes").addEventListener("click", () => {
  if (!pendingResolveId) return;

  fetch(`/admin/issues/approve/${pendingResolveId}`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
      document.getElementById("resolve-modal").classList.add("hidden");

      if (data.success) {
        showFlash("✅ Issue approved!"); // ✅ updated
        fetchIssueReports();
      } else {
        alert("⚠️ Failed to approve issue: " + (data.error || "Unknown error"));
      }
    })
    .catch(err => {
      console.error("❌ Error approving issue:", err);
      alert("Something went wrong.");
    });

  pendingResolveId = null;
});

// Cancel approval modal
document.getElementById("resolve-no").addEventListener("click", () => {
  pendingResolveId = null;
  document.getElementById("resolve-modal").classList.add("hidden");
});

// Show success banner
function showFlash(message) {
  const banner = document.getElementById("flash-banner");
  if (!banner) return;

  banner.textContent = message;
  banner.classList.remove("hidden");

  setTimeout(() => {
    banner.classList.add("hidden");
  }, 3000);
}

// View user info modal
function viewCustomer(customerId) {
  fetch(`/admin/users/api/${customerId}`)
    .then(res => res.json())
    .then(user => {
      if (user && !user.error) {
        Promise.all([
          fetch(`/admin/users/${customerId}/report_count`).then(r => r.json()),
          fetch(`/admin/users/${customerId}/booking_count`).then(r => r.json())
        ]).then(([reportData, bookingData]) => {
          const reportCount = reportData.count ?? 0;
          const bookingCount = bookingData.count ?? 0;

          const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ");
          const displayName = fullName || "Name not provided";

          const container = document.getElementById("user-details");
          container.innerHTML = `
            <div class="profile-header">
              <div class="profile-avatar">👤</div>
              <h3>${user.username}</h3>
              <p class="text-secondary">${displayName}</p>
            </div>
            <div class="profile-fields">
              <p><strong>Email:</strong> ${user.email || "N/A"}</p>
              <p><strong>Phone:</strong> ${user.phone_number || "Not provided"}</p>
              <p><strong>Balance:</strong> $${user.balance ?? "0"}</p>
              <p><strong>Created At:</strong> ${formatDate(user.created_at)}</p>
              <p><strong>Issue Reports:</strong> ${reportCount}</p>
              <p><strong>Total Bookings:</strong> ${bookingCount}</p>
            </div>
          `;

          document.getElementById("user-modal").classList.remove("hidden");
        });
      } else {
        alert("User not found.");
      }
    })
    .catch(err => {
      console.error("❌ Failed to load user:", err);
      alert("Unable to load user info.");
    });
}

// Close modal
function closeModal() {
  document.getElementById("user-modal").classList.add("hidden");
}

// Format date string
function formatDate(dateStr) {
  const d = new Date(dateStr);
  return isNaN(d) ? "-" : d.toLocaleString();
}

// Initial load
window.onload = fetchIssueReports;
