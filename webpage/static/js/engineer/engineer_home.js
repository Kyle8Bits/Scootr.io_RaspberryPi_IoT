window.onload = () => {
    fetch("/engineer/home/api")
      .then(res => res.json())
      .then(data => {
        if (data.error) throw new Error(data.error);
  
        // Fill in stat cards
        document.getElementById("assigned-count").textContent = data.assigned_scooters;
        document.getElementById("resolved-count").textContent = data.resolved_issues;
        document.getElementById("battery-avg").textContent = data.average_battery;
        document.getElementById("lowest-battery").textContent = data.lowest_battery;
  
        const avg = data.average_resolution_time;
        document.getElementById("avg-resolution").textContent =
          avg === "N/A" ? "No data" : avg;
  
        // Dashboard components
        renderStatusBadges(data.status_counts);
        renderResolutionList(data.recent_resolutions);
        renderResolutionChart(data.recent_resolutions);
        document.getElementById("top-resolution-type").textContent = getTopResolutionType(data.recent_resolutions);
      })
      .catch(err => {
        console.error("❌ Dashboard fetch error:", err);
      });
  };
  
  // ⬇️ Helpers
  function renderStatusBadges(statusCounts) {
    const container = document.getElementById("status-stats");
    container.innerHTML = "";
    if (!statusCounts) return;
  
    for (const [status, count] of Object.entries(statusCounts)) {
      const span = document.createElement("span");
      const cls = status.toLowerCase().replace(/\s+/g, "-");
      span.className = `status-badge ${cls}`;
      span.textContent = `${status}: ${count}`;
      container.appendChild(span);
    }
  }
  
  function renderResolutionList(resolutions) {
    const list = document.getElementById("recent-resolutions");
    list.innerHTML = "";
    resolutions.forEach(res => {
      const item = document.createElement("li");
      item.innerHTML = `🛠️ <strong>${res.issue_type.replaceAll("_", " ")}</strong> - Scooter #${res.scooter_id}<br/>
                        🕒 ${timeAgo(res.resolved_at)} | Type: ${res.resolution_type}`;
      list.appendChild(item);
    });
  }
  
  function renderResolutionChart(resolutions) {
    const ctx = document.getElementById("resolution-chart").getContext("2d");
    const counts = {};
    resolutions.forEach(r => {
      const type = r.resolution_type || "Unknown";
      counts[type] = (counts[type] || 0) + 1;
    });
  
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: Object.keys(counts),
        datasets: [{
          data: Object.values(counts),
          backgroundColor: [
            "#4caf50", "#2196f3", "#ffc107", "#ff5722",
            "#9c27b0", "#607d8b", "#f44336", "#00bcd4"
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
          title: { display: true, text: "Recent Resolution Types" }
        }
      }
    });
  }
  
  function timeAgo(str) {
    if (!str || str === "None") return "-";
    const past = new Date(str);
    const now = new Date();
    const diffMs = now - past;
    const minutes = Math.floor(diffMs / (1000 * 60));
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes} minute(s) ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour(s) ago`;
    const days = Math.floor(hours / 24);
    return `${days} day(s) ago`;
  }
  
  function getTopResolutionType(resolutions) {
    const counter = {};
    resolutions.forEach(r => {
      const type = r.resolution_type || "Other";
      counter[type] = (counter[type] || 0) + 1;
    });
  
    const sorted = Object.entries(counter).sort((a, b) => b[1] - a[1]);
    return sorted.length > 0 ? sorted[0][0].replaceAll("_", " ") : "-";
  }
  