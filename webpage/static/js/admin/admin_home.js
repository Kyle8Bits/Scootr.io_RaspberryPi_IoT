document.addEventListener("DOMContentLoaded", async () => {
    const chartToggle = document.getElementById("chart-toggle");
    const typeToggle = document.getElementById("type-toggle");
    const ridesDisplay = document.getElementById("total-rides");
    const revenueDisplay = document.getElementById("total-revenue");
    const customerDisplay = document.getElementById("total-customers");
    const scooterDisplay = document.getElementById("total-scooters");
  
    let chart;
    let currentView = "daily";
    let currentType = "bar";
  
    await fetchChartData(currentView, currentType);
    await fetchTopScootersChart();
    await fetchMetrics();
  
    chartToggle.addEventListener("change", async () => {
      currentView = chartToggle.value;
      await fetchChartData(currentView, currentType);
    });

    typeToggle.addEventListener("change", async () => {
      currentType = typeToggle.value;
      await fetchChartData(currentView, currentType);
    });

  
    document.getElementById("downloadChart").addEventListener("click", () => {
      const link = document.createElement("a");
      link.download = `scooter-usage-${currentView}.png`;
      link.href = document.getElementById("usageChart").toDataURL();
      link.click();
    });
  
   async function fetchChartData(view, type) {
      try {
        const res = await fetch(`/admin/analytics?view=${view}`);
        const data = await res.json();

        const labels = Array.isArray(data.labels) ? data.labels : [];
        const values = Array.isArray(data.values) ? data.values : [];

        ridesDisplay.textContent = data.total_rides || 0;
        revenueDisplay.textContent = `$${(data.total_revenue || 0).toFixed(2)}`;

        const prev = values.length > 1 ? values[values.length - 2] : 0;
        const latest = values.length > 0 ? values[values.length - 1] : 0;

        let summary = "⚖️ No change.";
        if (prev !== 0) {
          const change = ((latest - prev) / prev) * 100;
          if (change > 0) summary = `📈 Ride activity increased by ${change.toFixed(1)}%.`;
          else if (change < 0) summary = `📉 Ride activity decreased by ${Math.abs(change).toFixed(1)}%.`;
        }
        document.getElementById("chart-summary").textContent = summary;

        if (chart) chart.destroy();

        chart = new Chart(document.getElementById("usageChart"), {
          type: type,
          data: {
            labels: labels,
            datasets: [{
              label: "Scooter Rides",
              data: values,
              backgroundColor: values.map((_, i) =>
                i === values.length - 1 ? "#C66FA0" : "rgba(43, 63, 174, 0.6)"
              ),
              borderColor: "#2B3FAE",
              borderWidth: 2,
              fill: type === "line" ? false : true,
              tension: 0.3,
              pointRadius: 5,
              pointHoverRadius: 7
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: ctx => `Rides: ${ctx.parsed.y}`
                }
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                title: { display: true, text: "Rides" }
              },
              x: {
                title: { display: true, text: view === "daily" ? "Date" : "Week" }






              }
            }
          }



        });
      } catch (err) {
        console.error("❌ Failed to load analytics:", err);
      }
    }


  async function fetchTopScootersChart() {
    try {
      const res = await fetch("/admin/top_scooters");
      const data = await res.json();

      const ctx = document.getElementById("topScootersChart");
      new Chart(ctx, {
        type: "bar",
        data: {
          labels: data.labels,
          datasets: [{
            label: "Total Rides",
            data: data.values,
            backgroundColor: "#FDB679",
            borderColor: "#E39A7B",
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: { display: true, text: "Rides" }
            },
            x: {
              title: { display: true, text: "Scooter ID" }
            }
          }
        }
      });
    } catch (err) {
      console.error("❌ Failed to load top scooters:", err);
    }
  }

  async function fetchMetrics() {
    try {
      const res = await fetch("/admin/metrics");
      const data = await res.json();

      customerDisplay.textContent = data.customers;
      scooterDisplay.textContent = data.scooters;
    } catch (err) {
      console.error("❌ Failed to load metrics:", err);
    }
  }
});