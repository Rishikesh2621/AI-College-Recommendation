(function () {
  const panels = Array.from(document.querySelectorAll(".wizard-panel"));
  const stepButtons = Array.from(document.querySelectorAll(".wizard-step"));
  const nextButton = document.querySelector("[data-wizard-next]");
  const prevButton = document.querySelector("[data-wizard-prev]");
  const submitButton = document.querySelector(".wizard-actions button[type='submit']");
  let currentStep = 0;

  function showStep(index) {
    if (!panels.length) return;
    currentStep = Math.max(0, Math.min(index, panels.length - 1));
    panels.forEach((panel, panelIndex) => panel.classList.toggle("active", panelIndex === currentStep));
    stepButtons.forEach((button, buttonIndex) => button.classList.toggle("active", buttonIndex === currentStep));
    if (prevButton) prevButton.disabled = currentStep === 0;
    if (nextButton) nextButton.classList.toggle("d-none", currentStep === panels.length - 1);
    if (submitButton) submitButton.classList.toggle("d-none", currentStep !== panels.length - 1);
  }

  stepButtons.forEach((button) => {
    button.addEventListener("click", () => showStep(Number(button.dataset.stepTarget)));
  });
  if (nextButton) nextButton.addEventListener("click", () => showStep(currentStep + 1));
  if (prevButton) prevButton.addEventListener("click", () => showStep(currentStep - 1));
  showStep(0);

  function chart(id, config) {
    const element = document.getElementById(id);
    if (!element || typeof Chart === "undefined") return;
    return new Chart(element, config);
  }

  const data = window.COLLEGE_CHARTS;
  if (data && typeof Chart !== "undefined") {
    const palette = ["#2563eb", "#0f766e", "#f59e0b", "#e11d48", "#7c3aed", "#0891b2"];
    const chartText = "#475569";
    const chartGrid = "#e5edf7";
    Chart.defaults.color = chartText;
    Chart.defaults.font.family = 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    Chart.defaults.plugins.legend.labels.boxWidth = 12;
    Chart.defaults.plugins.legend.labels.boxHeight = 12;
    const legendOptions = {
      labels: {
        color: chartText,
        padding: 16,
        usePointStyle: true,
        pointStyle: "circle"
      }
    };
    const axisOptions = {
      ticks: { color: chartText, maxRotation: 0, autoSkip: true },
      grid: { color: chartGrid, drawBorder: false }
    };
    chart("probabilityChart", {
      type: "doughnut",
      data: { labels: data.probabilities.labels, datasets: [{ data: data.probabilities.values, backgroundColor: palette, borderColor: "#ffffff", borderWidth: 3 }] },
      options: { responsive: true, maintainAspectRatio: false, cutout: "62%", plugins: { legend: legendOptions } }
    });
    chart("feeChart", {
      type: "bar",
      data: { labels: data.fees.labels, datasets: [{ label: "Fees", data: data.fees.values, backgroundColor: "#f59e0b", borderRadius: 8, maxBarThickness: 38 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: axisOptions, y: axisOptions } }
    });
    chart("placementChart", {
      type: "bar",
      data: { labels: data.placements.labels, datasets: [{ label: "Placement %", data: data.placements.values, backgroundColor: "#0f766e", borderRadius: 8, maxBarThickness: 38 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: axisOptions, y: axisOptions } }
    });
    chart("rankingChart", {
      type: "line",
      data: { labels: data.ranking.labels, datasets: [{ label: "Admission Probability", data: data.ranking.values, borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,.12)", pointBackgroundColor: "#2563eb", pointBorderColor: "#ffffff", pointBorderWidth: 2, fill: true, tension: 0.35 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: legendOptions }, scales: { x: axisOptions, y: axisOptions } }
    });
    chart("branchChart", {
      type: "pie",
      data: { labels: data.branches.labels, datasets: [{ data: data.branches.values, backgroundColor: palette, borderColor: "#ffffff", borderWidth: 3 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: legendOptions } }
    });
    document.body.classList.add("charts-rendered");
  }

  const filterControls = Array.from(document.querySelectorAll("[data-filter]"));
  const collegeRows = document.getElementById("collegeRows");

  function renderRows(rows) {
    if (!collegeRows) return;
    if (!rows.length) {
      collegeRows.innerHTML = "<tr><td colspan='8' class='text-center py-4'>No colleges matched the selected filters.</td></tr>";
      return;
    }
    collegeRows.innerHTML = rows.map((college) => `
      <tr>
        <td><strong>${college["College Name"]}</strong><br><small>${college["NAAC Grade"]} • NBA ${college.NBA}</small></td>
        <td>${college.City}</td>
        <td>${college.Branch}</td>
        <td>${college["Closing Percentile"]}</td>
        <td><span class="chance-pill">${college.chance || 'Filtered'}</span></td>
        <td>${Number(college.Fees) > 0 ? `Rs. ${Number(college.Fees).toLocaleString("en-IN")}` : "Not provided"}</td>
        <td>${Number(college["Placement Percentage"]) > 0 ? `${college["Placement Percentage"]}%` : "Not provided"}</td>
        <td><a href="${college.Website}" target="_blank" rel="noreferrer">Visit</a></td>
      </tr>
    `).join("");
  }

  async function refreshFilters() {
    if (!filterControls.length) return;
    const params = new URLSearchParams();
    filterControls.forEach((control) => {
      if (control.value) params.set(control.dataset.filter, control.value);
    });
    const filterBar = document.querySelector(".filter-bar");
    if (filterBar) {
      if (filterBar.dataset.category) params.set("category", filterBar.dataset.category);
      if (filterBar.dataset.percentile) params.set("percentile", filterBar.dataset.percentile);
    }
    const response = await fetch(`/api/filters?${params.toString()}`);
    renderRows(await response.json());
  }

  filterControls.forEach((control) => control.addEventListener("change", refreshFilters));
})();
