import { useState, useEffect } from "react";
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  LineChart, Line,
  AreaChart, Area,
  ScatterChart, Scatter, ZAxis,
} from "recharts";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("fake_review_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ─── Colours ──────────────────────────────────────────────────────────────────
const C = {
  fake:    "#e05555",   // soft red — still clearly error
  genuine: "#2a9d8f",  // teal — matches theme accent
  pending: "#d4a017",  // warm amber
  accent:  "#2a9d8f",  // butter teal accent
  muted:   "#5abcb0",  // soft teal muted
  bg:      "#f5fcfa",  // near-white teal bg
  card:    "#ffffff",  // white cards
  border:  "#a8d8d0",  // teal border
  text:    "#1a3d38",  // dark teal text
  sub:     "#1a6b5f",  // mid teal labels
};
const PIE_COLORS  = [C.genuine, C.fake, C.pending];
const BATCH_COLORS = [C.genuine, C.accent, C.fake, C.pending];

const tooltipStyle = {
  contentStyle: { background: C.card, border: `1px solid ${C.border}`, borderRadius: 8, color: C.text, fontSize: 12 },
  itemStyle: { color: C.text },
  labelStyle: { color: C.sub },
};

const CHART_HEIGHT = 220;

// ─── Shared components ────────────────────────────────────────────────────────
function Card({ title, children }) {
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "16px 20px" }}>
      {title && <p style={{ color: C.sub, fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 12 }}>{title}</p>}
      {children}
    </div>
  );
}

function KPIBadge({ label, value, color, sub }) {
  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: "18px 20px", display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ color: C.sub, fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</span>
      <span style={{ color, fontSize: 28, fontWeight: 800, lineHeight: 1 }}>{value ?? "—"}</span>
      {sub && <span style={{ color: C.muted, fontSize: 11 }}>{sub}</span>}
    </div>
  );
}

function Spinner() {
  return <div style={{ color: C.sub, fontSize: 13, padding: "40px 0", textAlign: "center" }}>Loading…</div>;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function AdminDashboardCharts({ user, navigate }) {
  const [tab, setTab] = useState("overview");

  // Raw API data
  const [stats,    setStats]    = useState(null);   // /api/shop/stats/reviews  → { total, fake, genuine, by_product }
  const [reviews,  setReviews]  = useState([]);      // /api/reviews             → ReviewOut[]
  const [users,    setUsers]    = useState([]);      // /api/admin/users         → UserOut[]
  const [batches,  setBatches]  = useState([]);      // /api/shop/upload/batches → UploadBatchOut[]
  const [audit,    setAudit]    = useState([]);      // /api/audit               → AuditLogOut[]
  const [flagged,  setFlagged]  = useState([]);      // /api/reviews/flagged     → ReviewOut[]
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  useEffect(() => {
    if (!user?.is_admin) { navigate("/reviewguard/login"); return; }
    fetchAll(true);
  }, [user]);

  async function fetchAll(isInitial = false) {
    if (isInitial) setLoading(true);
    else setRefreshing(true);

    try {
      await Promise.all([
        fetch(`${API}/api/shop/stats/reviews`,        { headers: authHeaders() }).then(r => r.ok ? r.json() : null).then(d => d && setStats(d)).catch(()=>{}),
        fetch(`${API}/api/reviews?limit=100`,         { headers: authHeaders() }).then(r => r.ok ? r.json() : []).then(setReviews).catch(()=>{}),
        fetch(`${API}/api/admin/users`,               { headers: authHeaders() }).then(r => r.ok ? r.json() : []).then(setUsers).catch(()=>{}),
        fetch(`${API}/api/shop/upload/batches`,       { headers: authHeaders() }).then(r => r.ok ? r.json() : []).then(setBatches).catch(()=>{}),
        fetch(`${API}/api/audit?page=1&page_size=200`,{ headers: authHeaders() }).then(r => r.ok ? r.json() : { items: [] }).then(d => setAudit(d.items || [])).catch(()=>{}),
        fetch(`${API}/api/reviews/flagged?limit=100`, { headers: authHeaders() }).then(r => r.ok ? r.json() : []).then(setFlagged).catch(()=>{}),
      ]);
    } catch(e) { console.error('fetchAll error:', e); }

    setLoading(false);
    setRefreshing(false);
    setLastRefreshed(new Date());
  }

  // ── Derived data computed from real API responses ──────────────────────────

  // Verdict pie  →  stats endpoint gives totals directly
  const verdictPie = stats ? [
    { name: "Genuine", value: stats.genuine },
    { name: "Fake",    value: stats.fake },
    { name: "Pending", value: stats.total - stats.fake - stats.genuine },
  ] : [];

  // Per-product bar  →  stats.by_product: [{ product, total, fake }]
  const byProduct = (stats?.by_product || []).map(p => ({
    product: p.product,
    Genuine: p.total - p.fake,
    Fake:    p.fake,
  }));

  // Review trend by day  →  derived from reviews[].created_at
  const trendMap = {};
  reviews.forEach(r => {
    const day = new Date(r.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
    if (!trendMap[day]) trendMap[day] = { date: day, Fake: 0, Genuine: 0, Pending: 0 };
    if (r.verdict === "fake")    trendMap[day].Fake++;
    else if (r.verdict === "genuine") trendMap[day].Genuine++;
    else                         trendMap[day].Pending++;
  });
  const reviewsTrend = Object.values(trendMap).slice(-14);

  // Confidence histogram  →  from reviews[].confidence (0–1 float)
  const confBuckets = Array.from({ length: 10 }, (_, i) => ({
    range: `${i * 10}–${i * 10 + 10}%`,
    Fake: 0, Genuine: 0,
  }));
  reviews.forEach(r => {
    if (r.confidence == null || !r.verdict) return;
    const bucket = Math.min(Math.floor(r.confidence * 10), 9);
    if (r.verdict === "fake")    confBuckets[bucket].Fake++;
    else if (r.verdict === "genuine") confBuckets[bucket].Genuine++;
  });

  // Scatter: confidence vs rating  →  reviews[].confidence + reviews[].rating
  const scatterFake    = reviews.filter(r => r.verdict === "fake"    && r.confidence != null && r.rating != null)
    .map(r => ({ confidence: Math.round(r.confidence * 100), rating: r.rating, z: 10 }));
  const scatterGenuine = reviews.filter(r => r.verdict === "genuine" && r.confidence != null && r.rating != null)
    .map(r => ({ confidence: Math.round(r.confidence * 100), rating: r.rating, z: 10 }));

  // Flag reasons  →  reviews[].flag_reason (string)
  const flagReasonMap = {};
  flagged.forEach(r => {
    const reason = r.flag_reason || "Unspecified";
    flagReasonMap[reason] = (flagReasonMap[reason] || 0) + 1;
  });
  const flagReasons = Object.entries(flagReasonMap)
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count);

  // User roles  →  users[].role + users[].is_admin
  const roleMap = { User: 0, Owner: 0, Admin: 0 };
  users.forEach(u => {
    if (u.is_admin) roleMap.Admin++;
    else if (u.role === "Owner") roleMap.Owner++;
    else roleMap.User++;
  });
  const userRoles = Object.entries(roleMap).map(([name, value]) => ({ name, value }));

  // Active vs inactive  →  users[].is_active (field NOT in UserOut schema — shown as note)
  // UserOut doesn't expose is_active, so we count by role availability only
  const activeCount   = users.length; // all returned users are accessible
  // (is_active is not in UserOut schema — backend would need to expose it)

  // User signups by day  →  users[].created_at
  const signupMap = {};
  users.forEach(u => {
    const day = new Date(u.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
    signupMap[day] = (signupMap[day] || 0) + 1;
  });
  const userSignups = Object.entries(signupMap)
    .map(([date, Users]) => ({ date, Users }))
    .slice(-30);

  // Batch status pie  →  batches[].status
  const batchMap = { completed: 0, processing: 0, failed: 0, pending: 0 };
  batches.forEach(b => { if (batchMap[b.status] !== undefined) batchMap[b.status]++; });
  const batchStatus = [
    { name: "Completed",  value: batchMap.completed  },
    { name: "Processing", value: batchMap.processing },
    { name: "Failed",     value: batchMap.failed     },
    { name: "Pending",    value: batchMap.pending    },
  ].filter(b => b.value > 0);

  // Batch success rate over time  →  batches[].success_rows / total_rows
  const batchTrend = batches.slice(-10).map((b, i) => ({
    batch: `#${b.id}`,
    Success: b.total_rows > 0 ? Math.round((b.success_rows / b.total_rows) * 100) : 0,
    Failure: b.total_rows > 0 ? Math.round((b.failed_rows  / b.total_rows) * 100) : 0,
  }));

  // Audit actions breakdown  →  audit[].action
  const auditMap = {};
  audit.forEach(a => { auditMap[a.action] = (auditMap[a.action] || 0) + 1; });
  const auditActions = Object.entries(auditMap)
    .map(([action, count]) => ({ action, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  // KPIs
  const fakeRate   = stats?.total ? ((stats.fake / stats.total) * 100).toFixed(1) + "%" : "—";
  const avgConf    = reviews.filter(r => r.confidence != null).length
    ? (reviews.filter(r => r.confidence != null).reduce((s, r) => s + r.confidence, 0)
       / reviews.filter(r => r.confidence != null).length * 100).toFixed(1) + "%"
    : "—";

  const tabs = [
    { id: "overview",   label: "Overview" },
    { id: "reviews",    label: "Review Analytics" },
    { id: "users",      label: "User Analytics" },
    { id: "operations", label: "Operations" },
  ];

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text, fontFamily: "'DM Sans','Segoe UI',sans-serif", padding: 24 }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg,#2a9d8f,#a8d8d0)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🛡️</div>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 800, margin: 0, color: "#000000" }}>Admin Analytics Dashboard</h1>
          <p style={{ margin: 0, fontSize: 12, color: C.sub }}>Live data from your database</p>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
          <button onClick={() => navigate('/reviewguard')} style={{ background: "transparent", border: "1px solid #a8d8d0", color: "#1a6b5f", borderRadius: 8, padding: "6px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>🛡️ AI Detection</button>
          <button onClick={() => navigate('/admin')} style={{ background: "transparent", border: "1px solid #a8d8d0", color: "#1a6b5f", borderRadius: 8, padding: "6px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>⚙️ Admin</button>
          <button onClick={() => { localStorage.removeItem('fake_review_token'); navigate('/') }} style={{ background: "#ffffff", border: "1px solid #a8d8d0", color: "#1a6b5f", borderRadius: 8, padding: "6px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>Logout</button>
          {lastRefreshed && !refreshing && (
            <span style={{ fontSize: 11, color: C.sub }}>
              Last updated: {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
          {refreshing && (
            <span style={{ fontSize: 11, color: C.accent }}>Refreshing…</span>
          )}
          <button
            onClick={() => fetchAll(false)}
            disabled={refreshing}
            style={{
              background: refreshing ? C.muted : C.accent,
              border: `1px solid ${refreshing ? C.border : C.accent}`,
              color: "#ffffff",
              borderRadius: 8, padding: "6px 16px", fontSize: 13,
              cursor: refreshing ? "not-allowed" : "pointer",
              fontWeight: 600, transition: "all .15s",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            <span style={{ display: "inline-block", animation: refreshing ? "spin 1s linear infinite" : "none" }}>↻</span>
            {refreshing ? "Refreshing" : "Refresh"}
          </button>
        </div>
        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 24, borderBottom: `1px solid ${C.border}` }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{ background: "transparent", border: "none", cursor: "pointer", padding: "8px 16px", fontSize: 13, fontWeight: 600,
              color: tab === t.id ? "#818cf8" : C.sub,
              borderBottom: tab === t.id ? "2px solid #818cf8" : "2px solid transparent", transition: "all .15s" }}>
            {t.label}
          </button>
        ))}
      </div>

      {loading && <Spinner />}

      {/* ── OVERVIEW ──────────────────────────────────────────────────────── */}
      {!loading && tab === "overview" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(150px,1fr))", gap: 12 }}>
            <KPIBadge label="Total Reviews"  value={stats?.total}   color="#1a3d38"  sub="All time" />
            <KPIBadge label="Genuine"        value={stats?.genuine} color={C.genuine} sub="Verified clean" />
            <KPIBadge label="Fake"           value={stats?.fake}    color={C.fake}    sub="Detected" />
            <KPIBadge label="Pending"        value={stats ? stats.total - stats.fake - stats.genuine : null} color={C.pending} sub="No verdict yet" />
            <KPIBadge label="Fake Rate"      value={fakeRate}       color="#d4a017"  sub="Of classified" />
            <KPIBadge label="Avg Confidence" value={avgConf}        color={C.accent}  sub="Model certainty" />
            <KPIBadge label="Flagged"        value={flagged.length} color="#e05555"  sub="Need review" />
            <KPIBadge label="Users"          value={users.length}   color="#2a9d8f"  sub="Registered" />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 16 }}>
            <Card title="Verdict Distribution">
              <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                <PieChart>
                  <Pie data={verdictPie} dataKey="value" cx="50%" cy="50%" outerRadius={80}
                    label={({ name, percent }) => percent > 0 ? `${name} ${(percent * 100).toFixed(0)}%` : ""}
                    labelLine={false} style={{ fontSize: 11 }}>
                    {verdictPie.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                  </Pie>
                  <Tooltip {...tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Review Volume Trend (last 14 days)">
              <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                <AreaChart data={reviewsTrend} margin={{ left: -10 }}>
                  <defs>
                    <linearGradient id="gGenuine" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={C.genuine} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={C.genuine} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gFake" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={C.fake} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={C.fake} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                  <XAxis dataKey="date" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} />
                  <YAxis tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip {...tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: 12, color: C.sub }} />
                  <Area type="monotone" dataKey="Genuine" stroke={C.genuine} fill="url(#gGenuine)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="Fake"    stroke={C.fake}    fill="url(#gFake)"    strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>

          <Card title="Fake vs Genuine per Product (from stats API)">
            {byProduct.length === 0
              ? <p style={{ color: C.sub, fontSize: 12 }}>No product data yet.</p>
              : <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={byProduct} margin={{ left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                    <XAxis dataKey="product" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} />
                    <YAxis tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip {...tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 12, color: C.sub }} />
                    <Bar dataKey="Genuine" fill={C.genuine} radius={[4,4,0,0]} />
                    <Bar dataKey="Fake"    fill={C.fake}    radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
            }
          </Card>
        </div>
      )}

      {/* ── REVIEW ANALYTICS ──────────────────────────────────────────────── */}
      {!loading && tab === "reviews" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <Card title="Model Confidence Distribution — last 100 reviews (reviews[].confidence)">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={confBuckets} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                <XAxis dataKey="range" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} />
                <YAxis tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip {...tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: C.sub }} />
                <Bar dataKey="Genuine" fill={C.genuine} radius={[3,3,0,0]} />
                <Bar dataKey="Fake"    fill={C.fake}    radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
            <p style={{ color: C.sub, fontSize: 11, marginTop: 8 }}>
              Derived from <code>reviews[].confidence</code> (float 0–1) and <code>reviews[].verdict</code>.
            </p>
          </Card>

          <Card title="Confidence vs Star Rating (reviews[].confidence + reviews[].rating)">
            {(scatterFake.length + scatterGenuine.length) === 0
              ? <p style={{ color: C.sub, fontSize: 12 }}>Not enough classified reviews with both confidence and rating.</p>
              : <ResponsiveContainer width="100%" height={260}>
                  <ScatterChart margin={{ left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                    <XAxis type="number" dataKey="confidence" name="Confidence" unit="%" tick={{ fill: C.sub, fontSize: 10 }} domain={[0, 100]} />
                    <YAxis type="number" dataKey="rating"     name="Stars"      tick={{ fill: C.sub, fontSize: 10 }} domain={[0, 6]} ticks={[1,2,3,4,5]} />
                    <ZAxis dataKey="z" range={[30, 80]} />
                    <Tooltip {...tooltipStyle} cursor={{ strokeDasharray: "3 3" }} />
                    <Legend wrapperStyle={{ fontSize: 12, color: C.sub }} />
                    <Scatter name="Fake"    data={scatterFake}    fill={C.fake}    fillOpacity={0.7} />
                    <Scatter name="Genuine" data={scatterGenuine} fill={C.genuine} fillOpacity={0.6} />
                  </ScatterChart>
                </ResponsiveContainer>
            }
          </Card>

          <Card title="Flag Reasons (reviews/flagged[].flag_reason)">
            {flagReasons.length === 0
              ? <p style={{ color: C.sub, fontSize: 12 }}>No flagged reviews yet.</p>
              : <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={flagReasons} layout="vertical" margin={{ left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.border} horizontal={false} />
                    <XAxis type="number" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis type="category" dataKey="reason" tick={{ fill: C.text, fontSize: 11 }} tickLine={false} width={100} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="count" fill={C.accent} radius={[0,4,4,0]} />
                  </BarChart>
                </ResponsiveContainer>
            }
          </Card>
        </div>
      )}

      {/* ── USER ANALYTICS ────────────────────────────────────────────────── */}
      {!loading && tab === "users" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card title="User Role Distribution (users[].role + is_admin)">
              <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                <PieChart>
                  <Pie data={userRoles} dataKey="value" cx="50%" cy="50%"
                    innerRadius={50} outerRadius={80}
                    label={({ name, value }) => `${name}: ${value}`} labelLine>
                    {userRoles.map((_, i) => <Cell key={i} fill={[C.accent, C.pending, C.genuine][i]} />)}
                  </Pie>
                  <Tooltip {...tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Total Registered Users">
              <div style={{ display: "flex", flexDirection: "column", gap: 12, paddingTop: 8 }}>
                {userRoles.map((r, i) => (
                  <div key={r.name} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 10, height: 10, borderRadius: "50%", background: [C.accent, C.pending, C.genuine][i], flexShrink: 0 }} />
                    <span style={{ color: C.text, fontSize: 13, flex: 1 }}>{r.name}</span>
                    <span style={{ color: [C.accent, C.pending, C.genuine][i], fontWeight: 700, fontSize: 16 }}>{r.value}</span>
                    <div style={{ flex: 2, background: C.border, borderRadius: 4, height: 6 }}>
                      <div style={{ width: `${users.length ? (r.value / users.length) * 100 : 0}%`, background: [C.accent, C.pending, C.genuine][i], height: "100%", borderRadius: 4 }} />
                    </div>
                  </div>
                ))}
                <div style={{ marginTop: 8, borderTop: `1px solid ${C.border}`, paddingTop: 8, color: C.sub, fontSize: 12 }}>
                  Total: <strong style={{ color: C.text }}>{users.length}</strong> users from <code style={{ fontSize: 11 }}>/api/admin/users</code>
                </div>
              </div>
            </Card>
          </div>

          <Card title="User Signups Over Time (users[].created_at)">
            {userSignups.length === 0
              ? <p style={{ color: C.sub, fontSize: 12 }}>No signup data yet.</p>
              : <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={userSignups} margin={{ left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                    <XAxis dataKey="date" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} />
                    <YAxis tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip {...tooltipStyle} />
                    <Line type="monotone" dataKey="Users" stroke="#2a9d8f" strokeWidth={2} dot={{ r: 3, fill: "#2a9d8f" }} />
                  </LineChart>
                </ResponsiveContainer>
            }
          </Card>
        </div>
      )}

      {/* ── OPERATIONS ────────────────────────────────────────────────────── */}
      {!loading && tab === "operations" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card title="Upload Batch Status (batches[].status)">
              {batchStatus.length === 0
                ? <p style={{ color: C.sub, fontSize: 12 }}>No batches uploaded yet.</p>
                : <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                    <PieChart>
                      <Pie data={batchStatus} dataKey="value" cx="50%" cy="50%"
                        outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
                        {batchStatus.map((_, i) => <Cell key={i} fill={BATCH_COLORS[i]} />)}
                      </Pie>
                      <Tooltip {...tooltipStyle} />
                    </PieChart>
                  </ResponsiveContainer>
              }
            </Card>

            <Card title="Audit Actions Breakdown (audit[].action)">
              {auditActions.length === 0
                ? <p style={{ color: C.sub, fontSize: 12 }}>No audit logs yet.</p>
                : <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
                    <BarChart data={auditActions} margin={{ left: -10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                      <XAxis dataKey="action" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} />
                      <YAxis tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} />
                      <Tooltip {...tooltipStyle} />
                      <Bar dataKey="count" fill={C.accent} radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
              }
            </Card>
          </div>

          <Card title="Batch Success vs Failure Rate (batches[].success_rows / total_rows)">
            {batchTrend.length === 0
              ? <p style={{ color: C.sub, fontSize: 12 }}>No batch data yet.</p>
              : <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={batchTrend} margin={{ left: -10 }}>
                    <defs>
                      <linearGradient id="gSuccess" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={C.genuine} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={C.genuine} stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="gFailure" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={C.fake} stopOpacity={0.4} />
                        <stop offset="95%" stopColor={C.fake} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
                    <XAxis dataKey="batch" tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} />
                    <YAxis tick={{ fill: C.sub, fontSize: 10 }} tickLine={false} axisLine={false} unit="%" />
                    <Tooltip {...tooltipStyle} formatter={v => [`${v}%`]} />
                    <Legend wrapperStyle={{ fontSize: 12, color: C.sub }} />
                    <Area type="monotone" dataKey="Success" stroke={C.genuine} fill="url(#gSuccess)" strokeWidth={2} />
                    <Area type="monotone" dataKey="Failure" stroke={C.fake}    fill="url(#gFailure)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
            }
          </Card>
        </div>
      )}
    </div>
  );
}
