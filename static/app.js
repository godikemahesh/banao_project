// Vireo Pulse — Operations Intelligence Frontend Application Logic

let teamChart = null;
let categoryChart = null;
let resTimeChart = null;
let slaBreachChart = null;
let globalMonthlyData = null;
let globalWorkloadData = null;

// Preset sample customer tickets
const SAMPLE_TICKETS = {
  1: {
    msg: "paid, confirmed, then nothing. 5 days and counting. VR885310",
    initial: "Billing & Payments"
  },
  2: {
    msg: "I was charged twice on my credit card for order VR898711. Please refund the duplicate amount.",
    initial: "Billing & Payments"
  },
  3: {
    msg: "Need tax invoice with my company's GSTIN number included for corporate filing.",
    initial: "Billing & Payments"
  },
  4: {
    msg: "Left earbud battery drains within 25 minutes while right earbud stays at 80%. Pulse 2.",
    initial: "Charging & Battery"
  },
  5: {
    msg: "Earbuds keep unpairing and disconnecting from phone whenever I walk outside.",
    initial: "Connectivity"
  }
};

// Simulation scenarios
const SCENARIOS = {
  A: {
    resTime: "25.1 hrs",
    resDesc: "No change. Logistics remains in operational crisis, handling 515 tickets/agent.",
    workload: "515 tickets",
    workloadDesc: "Logistics agents remain severely overloaded; Billing agents underutilized.",
    savings: "Rs 0 / yr",
    savingsDesc: "Transfer re-handling friction and SLA breach credits continue unabated.",
    netRoi: "-Rs 9.00 Lakh / yr",
    netDesc: "Full Rs 9L spent on Billing where tickets are already resolved in 41 minutes (0% ROI)."
  },
  B: {
    resTime: "7.8 hrs",
    resDesc: "Slashed from 25.1 hours to under 8 hours. Enables same-day customer resolution.",
    workload: "367 tickets",
    workloadDesc: "Workload drops by 29% from 515 down to 367 tickets/agent, resolving burnout.",
    savings: "Rs 0 / yr",
    savingsDesc: "Relieves capacity bottleneck, but process transfer friction remains until bot is fixed.",
    netRoi: "High Operational ROI",
    netDesc: "Saves customer retention and avoids brand churn in consumer audio wearables."
  },
  C: {
    resTime: "18.4 hrs",
    resDesc: "Eliminates the +17.8 hr hand-off penalty on 696 misrouted tickets.",
    workload: "515 tickets",
    workloadDesc: "Logistics receives tickets directly instead of after 2 days in Billing queue.",
    savings: "Rs 4.89 Lakh / yr",
    savingsDesc: "Eliminates 1,200+ avoidable transfers (Rs 305/xfer) and Rs 350 SLA breach credits.",
    netRoi: "+Rs 4.89 Lakh / yr",
    netDesc: "Pure process savings with $0 capital investment (Arjun Mehta's ideal preference)."
  },
  D: {
    resTime: "4.5 hrs",
    resDesc: "World-class turnaround: Same-shift resolution across all logistics inquiries.",
    workload: "367 tickets",
    workloadDesc: "Ideal sustainable capacity: 367 tickets/agent with zero re-handling friction.",
    savings: "Rs 4.89 Lakh / yr",
    savingsDesc: "Full administrative transfer costs and SLA penalties eliminated permanently.",
    netRoi: "Net -Rs 4.10 Lakh / yr",
    netDesc: "Direct process savings offset >54% of hiring budget! Less than the cost of 1 hire."
  }
};

document.addEventListener('DOMContentLoaded', () => {
  fetchOverviewData();
  fetchMonthlyTrends();
  fetchWorkloadAndPerformance();
  fetchExecutiveMemo();
});

// View Navigation Router
function navigate(viewKey) {
  document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.view-panel').forEach(panel => panel.classList.remove('active'));

  // Update nav buttons
  const navBtns = Array.from(document.querySelectorAll('.nav-item'));
  const targetBtn = navBtns.find(b => b.getAttribute('onclick')?.includes(viewKey));
  if (targetBtn) targetBtn.classList.add('active');

  // Update panels
  const targetPanel = document.getElementById(`view-${viewKey}`);
  if (targetPanel) targetPanel.classList.add('active');

  // Update title
  const titles = {
    overview: { t: "Executive Summary", s: "Strategic headcount allocation and root-cause analysis for Priya Raman & Arjun Mehta" },
    workload: { t: "Workload & Routing Intelligence", s: "Assigned intake volume vs. actual resolved workload across all 7 departments" },
    performance: { t: "SLA & Team Performance", s: "Operational resolution durations, throughput burden, and SLA breach audit" },
    sandbox: { t: "AI Triage Studio", s: "Interactive AI auto-categorization and routing disambiguation simulator" },
    simulator: { t: "Headcount & ROI Simulator", s: "Scenario modeling for Priya Raman & Arjun Mehta before signing off on requisitions" },
    memo: { t: "Executive Memorandum", s: "Complete formal briefing prepared for Head of CX Priya Raman (5-minute read)" }
  };

  const meta = titles[viewKey] || titles.overview;
  document.getElementById('page-title').textContent = meta.t;
  document.getElementById('page-subtitle').textContent = meta.s;
}

// Fetch Overview KPI Data
async function fetchOverviewData() {
  try {
    const res = await fetch('/api/overview');
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('kpi-total-tickets').textContent = data.total_tickets.toLocaleString();
    document.getElementById('kpi-misrouted-tickets').textContent = `${data.total_misrouted.toLocaleString()} (${data.misrouted_pct}%)`;
    document.getElementById('kpi-bounce-count').textContent = `${data.billing_to_logistics_leak.toLocaleString()} orders`;
    document.getElementById('kpi-quarterly-waste').textContent = `Rs ${(data.quarterly_friction_inr / 100000).toFixed(2)} Lakh`;
  } catch (err) {
    console.error('Error fetching overview:', err);
  }
}

// Fetch Monthly Breakdown Data
async function fetchMonthlyTrends() {
  try {
    const res = await fetch('/api/monthly-data');
    if (!res.ok) return;
    globalMonthlyData = await res.json();

    renderTeamComparisonChart(globalMonthlyData);
    renderCategoryChart(globalMonthlyData);
  } catch (err) {
    console.error('Error fetching monthly data:', err);
  }
}

function renderTeamComparisonChart(data) {
  const ctx = document.getElementById('teamComparisonChart')?.getContext('2d');
  if (!ctx) return;

  const months = data.months;
  const billingAssigned = data.teams_assigned["Billing"] || [];
  const billingResolved = data.teams_resolved["Billing"] || [];
  const logAssigned = data.teams_assigned["Logistics"] || [];
  const logResolved = data.teams_resolved["Logistics"] || [];

  if (teamChart) teamChart.destroy();

  teamChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Billing Intake (Priya\'s View)',
          data: billingAssigned,
          backgroundColor: 'rgba(147, 197, 253, 0.75)',
          borderColor: '#3b82f6',
          borderWidth: 1
        },
        {
          label: 'Billing Resolved (Actual Workload)',
          data: billingResolved,
          backgroundColor: '#1d4ed8',
          borderColor: '#1e40af',
          borderWidth: 1
        },
        {
          label: 'Logistics Intake Assigned',
          data: logAssigned,
          backgroundColor: 'rgba(254, 202, 202, 0.75)',
          borderColor: '#f87171',
          borderWidth: 1
        },
        {
          label: 'Logistics Resolved (+35% Surge)',
          data: logResolved,
          backgroundColor: '#b91c1c',
          borderColor: '#991b1b',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 14, font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' } } }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Monthly Tickets' } },
        x: { grid: { display: false } }
      }
    }
  });
}

function setTeamChartMode(mode, btn) {
  document.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  if (!teamChart) return;
  if (mode === 'assigned') {
    teamChart.data.datasets[0].hidden = false;
    teamChart.data.datasets[1].hidden = true;
    teamChart.data.datasets[2].hidden = false;
    teamChart.data.datasets[3].hidden = true;
  } else if (mode === 'resolved') {
    teamChart.data.datasets[0].hidden = true;
    teamChart.data.datasets[1].hidden = false;
    teamChart.data.datasets[2].hidden = true;
    teamChart.data.datasets[3].hidden = false;
  } else {
    teamChart.data.datasets.forEach(ds => ds.hidden = false);
  }
  teamChart.update();
}

function renderCategoryChart(data) {
  const ctx = document.getElementById('categoryChart')?.getContext('2d');
  if (!ctx) return;

  const months = data.months;
  const cats = data.categories;
  const palette = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16', '#6366f1', '#14b8a6', '#94a3b8'];

  const datasets = Object.keys(cats).map((catName, i) => ({
    label: catName,
    data: cats[catName],
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length],
    tension: 0.25,
    borderWidth: 2,
    pointRadius: 2.5
  }));

  if (categoryChart) categoryChart.destroy();

  categoryChart = new Chart(ctx, {
    type: 'line',
    data: { labels: months, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 12, font: { family: 'Plus Jakarta Sans', size: 10 } } }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Ticket Volume' } },
        x: { grid: { display: false } }
      }
    }
  });
}

// Fetch Workload and Render Performance Charts
async function fetchWorkloadAndPerformance() {
  try {
    const res = await fetch('/api/team-workload');
    if (!res.ok) return;
    const data = await res.json();
    globalWorkloadData = data.teams;

    // Render Table
    const tbody = document.getElementById('workload-table-body');
    if (tbody) {
      tbody.innerHTML = '';
      globalWorkloadData.forEach(t => {
        const tr = document.createElement('tr');
        const shiftPrefix = t.net_diff > 0 ? '+' : '';
        const shiftColor = t.net_diff > 0 ? 'text-red font-bold' : (t.net_diff < 0 ? 'text-blue font-bold' : '');
        
        tr.innerHTML = `
          <td><strong>${t.team}</strong></td>
          <td>${t.headcount}</td>
          <td>${t.assigned_intake.toLocaleString()} (${t.assigned_share_pct}%)</td>
          <td>${t.resolved_count.toLocaleString()} (${t.resolved_share_pct}%)</td>
          <td class="${shiftColor}">${shiftPrefix}${t.net_diff}</td>
          <td><strong>${t.tickets_per_agent}</strong></td>
          <td>${t.median_resolution_hours}h</td>
          <td>${t.sla_breaches}</td>
          <td><span class="badge ${t.sla_breach_rate_pct > 12 ? 'badge-red' : 'badge-green'}">${t.sla_breach_rate_pct}%</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    renderPerformanceCharts(globalWorkloadData);
  } catch (err) {
    console.error('Error fetching workload:', err);
  }
}

function renderPerformanceCharts(teams) {
  // Chart 1: Median Resolution Time
  const ctxRes = document.getElementById('resolutionTimeChart')?.getContext('2d');
  if (ctxRes) {
    const labels = teams.map(t => t.team);
    const times = teams.map(t => t.median_resolution_hours);

    if (resTimeChart) resTimeChart.destroy();
    resTimeChart = new Chart(ctxRes, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Median Hours',
          data: times,
          backgroundColor: '#6366f1',
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { title: { display: true, text: 'Hours' } } }
      }
    });
  }

  // Chart 2: SLA Breach Rate
  const ctxSla = document.getElementById('slaBreachChart')?.getContext('2d');
  if (ctxSla) {
    const labels = teams.map(t => t.team);
    const breaches = teams.map(t => t.sla_breach_rate_pct);

    if (slaBreachChart) slaBreachChart.destroy();
    slaBreachChart = new Chart(ctxSla, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'SLA Breach Rate (%)',
          data: breaches,
          backgroundColor: '#ef4444',
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { title: { display: true, text: 'Breach Rate %' }, max: 20 } }
      }
    });
  }
}

// AI Triage Sandbox Controls
function loadSampleTicket(id) {
  const sample = SAMPLE_TICKETS[id];
  if (!sample) return;
  document.getElementById('sandbox-input-msg').value = sample.msg;
  document.getElementById('sandbox-bot-tag').value = sample.initial;
  executeClassification();
}

async function executeClassification() {
  const msg = document.getElementById('sandbox-input-msg').value.trim();
  const botTag = document.getElementById('sandbox-bot-tag').value;

  if (!msg) {
    alert("Please enter a customer message.");
    return;
  }

  const btn = document.getElementById('btn-run-classifier');
  btn.disabled = true;
  btn.innerHTML = "<span>⏳</span> Analyzing Context...";

  try {
    const res = await fetch('/api/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, initial_category: botTag })
    });

    if (!res.ok) throw new Error("Inference failed");
    const result = await res.json();

    document.getElementById('out-placeholder').style.display = 'none';
    const outBox = document.getElementById('out-results');
    outBox.style.display = 'flex';

    document.getElementById('res-cat-title').textContent = result.predicted_category;
    document.getElementById('res-routing-badge').textContent = `Route to ${result.suggested_routing_team}`;
    
    const pct = Math.round(result.confidence * 100);
    document.getElementById('res-conf-num').textContent = `${pct}%`;
    document.getElementById('res-conf-bar').style.width = `${pct}%`;

    document.getElementById('res-evidence-quote').textContent = `"${result.evidence_quote}"`;
    document.getElementById('res-reasoning-text').textContent = result.routing_reason;

    const alertBanner = document.getElementById('res-uncertain-alert');
    alertBanner.style.display = result.uncertainty_flag ? 'block' : 'none';

  } catch (err) {
    console.error("Error classifying ticket:", err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = "<span>⚡</span> Run AI Classification &amp; Routing";
  }
}

// Headcount Simulator
function selectScenario(key, btn) {
  document.querySelectorAll('.sim-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const s = SCENARIOS[key];
  if (!s) return;

  document.getElementById('sim-res-time').textContent = s.resTime;
  document.getElementById('sim-res-desc').textContent = s.resDesc;

  document.getElementById('sim-workload').textContent = s.workload;
  document.getElementById('sim-workload-desc').textContent = s.workloadDesc;

  document.getElementById('sim-savings').textContent = s.savings;
  document.getElementById('sim-savings-desc').textContent = s.savingsDesc;

  document.getElementById('sim-net-roi').textContent = s.netRoi;
  document.getElementById('sim-net-desc').textContent = s.netDesc;
}

// Fetch Executive Memo Markdown
async function fetchExecutiveMemo() {
  const container = document.getElementById('memo-content-container');
  if (!container) return;

  const defaultMemoHtml = `
    <div class="memo-content">
      <div style="background: #f1f5f9; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.85rem;">
        <strong>TO:</strong> Priya Raman, Head of Customer Experience, Vireo Audio<br>
        <strong>FROM:</strong> Customer Operations & AI Engineering Team<br>
        <strong>DATE:</strong> September 29, 2026<br>
        <strong>SUBJECT:</strong> Headcount Allocation & Support Desk Audit: Resolving the "Billing Illusion"<br>
        <strong>READING TIME:</strong> ~5 minutes
      </div>

      <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 1.25rem; border-radius: 0 8px 8px 0; margin-bottom: 1.75rem;">
        <h4 style="color: #1e40af; margin-bottom: 0.4rem; font-size: 1rem;">Executive Summary: The Decision in 30 Seconds</h4>
        <p style="font-size: 0.95rem; font-weight: 600; color: #1e3a8a; margin-bottom: 0.5rem;">
          The Recommendation: Do NOT allocate the next two hires to Billing. Reassign them immediately to LOGISTICS.
        </p>
        <p style="font-size: 0.85rem; color: #334155; line-height: 1.5;">
          Your intake reports show Billing as your largest queue (20.8% of tickets / 2,425 assigned). However, our 18-month operational audit reveals this is an intake routing illusion: Billing resolves only 15.4% of actual workload (1,798 tickets). Meanwhile, Logistics receives 696+ transferred shipping complaints, resolves 2,574 tickets with only 5 agents (515/agent), and suffers a 25.1-hour median resolution time driving 16.4% SLA breaches.
        </p>
      </div>

      <h4 style="margin: 1.5rem 0 0.75rem 0;">1. The Numbers: Intake Queue vs. Operational Reality</h4>
      <table style="width:100%; border-collapse: collapse; margin-bottom: 1.5rem;">
        <thead>
          <tr style="background: #f8fafc;">
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Department</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Headcount</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Intake Assigned</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Actually Resolved</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Net Workload Shift</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Tickets / Agent</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Median Res Time</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">SLA Breach %</th>
          </tr>
        </thead>
        <tbody>
          <tr style="background: #eff6ff; font-weight: bold;">
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Billing</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">4</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">2,425 (20.8%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1,798 (15.4%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; color: #dc2626;">-627 (-25.9%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">449.5</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">0.68 hrs (41m)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">13.4%</td>
          </tr>
          <tr style="background: #fef2f2; font-weight: bold;">
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Logistics</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">5</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1,905 (16.4%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">2,574 (22.1%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; color: #16a34a;">+669 (+35.1%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">514.8</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; color: #dc2626;">25.1 hrs (1.05d)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0; color: #dc2626;">16.4%</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Chat Frontline</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">15</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">3,030 (26.0%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">3,078 (26.4%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">+48 (+1.6%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">205.2</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">0.43 hrs (26m)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">8.6%</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Email Frontline</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">7</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1,807 (15.5%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1,658 (14.2%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">-149 (-8.2%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">236.9</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1.83 hrs</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">9.5%</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Returns Desk</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">3</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1,049 (9.0%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">1,117 (9.6%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">+68 (+6.5%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">372.3</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">30.4 hrs</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">10.6%</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Voice Frontline</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">4</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">900 (7.7%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">766 (6.6%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">-134 (-14.9%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">191.5</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">0.68 hrs</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">4.6%</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Escalations & Wty</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">6</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">525 (4.5%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">650 (5.6%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">+125 (+23.8%)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">108.3</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">121.3 hrs</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">8.0%</td>
          </tr>
        </tbody>
      </table>

      <h4 style="margin: 1.5rem 0 0.5rem 0;">2. Why Billing's Queue is an Illusion</h4>
      <p style="font-size: 0.88rem; color: #334155; line-height: 1.6; margin-bottom: 1rem;">
        Neha Kulkarni noted: <em>"Billing keep telling me half their queue isn't theirs."</em> Our audit validates this: 47.4% of Billing's intake consists of delivery tracking complaints. Customers state: <em>"Payment was deducted 5 days ago, nothing arrived at my door"</em>. The chatbot catches "payment" and tags Billing. Billing agents open it, confirm payment, and bounce the ticket to Logistics. Tickets routed directly to Logistics resolve in 25 hours; tickets bounced through Billing take <strong>42.9 hours</strong> (+17.8 hour penalty).
      </p>

      <h4 style="margin: 1.5rem 0 0.5rem 0;">3. Arjun Mehta's Financial Case & Process ROI</h4>
      <p style="font-size: 0.88rem; color: #334155; line-height: 1.6; margin-bottom: 1rem;">
        Under Vireo's operating policy (§4), internal transfers cost <strong>Rs 305 per transfer</strong> in re-handling, and SLA breaches trigger <strong>Rs 350 store credit</strong> penalties (§3). Misrouting generates 327 bounced tickets every quarter. By fixing intake auto-categorization, Vireo saves <strong>Rs 1,22,295 per quarter (~Rs 4.89 Lakh per year)</strong>.
      </p>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
        <strong>The Investment Equation:</strong><br>
        • Annual Cost of 2 Hires: <strong>Rs 9,00,000 / yr</strong><br>
        • Process Savings from AI Routing: <strong>+Rs 4,89,180 / yr</strong><br>
        • Net Annual Spend to Fix Logistics: <strong>Rs 4,10,820 / yr</strong> (Less than the cost of 1 junior hire!)
      </div>
    </div>
  `;

  try {
    const res = await fetch('/api/memo');
    if (res.ok) {
      const data = await res.json();
      if (data.memo && data.memo.length > 50) {
        // Parse markdown if present
        let html = data.memo
          .replace(/^### (.*$)/gim, '<h3>$1</h3>')
          .replace(/^## (.*$)/gim, '<h2>$1</h2>')
          .replace(/^# (.*$)/gim, '<h1>$1</h1>')
          .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
          .replace(/\*(.*)\*/gim, '<em>$1</em>')
          .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');
        container.innerHTML = html;
        return;
      }
    }
  } catch (err) {
    console.warn("Using embedded memo fallback.");
  }
  container.innerHTML = defaultMemoHtml;
}
