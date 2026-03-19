<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
require_once 'includes/auth.php';
require_once 'includes/db.php';
require_login();

$pdo = get_pdo();
echo "Debug: PHP is running, logged in, DB connected<br>";

// Stat counts
function get_count(PDO $pdo, string $status): int {
    $stmt = $pdo->prepare("SELECT COUNT(*) FROM devices WHERE status = ?");
    $stmt->execute([$status]);
    return (int) $stmt->fetchColumn();
}
$total      = (int) $pdo->query("SELECT COUNT(*) FROM devices")->fetchColumn();
$allowed    = get_count($pdo, 'ALLOWED');
$blocked    = get_count($pdo, 'BLOCKED');
$quarantine = get_count($pdo, 'QUARANTINED');
$unknown    = get_count($pdo, 'UNKNOWN');
$alerts_pending = (int) $pdo->query("SELECT COUNT(*) FROM alerts WHERE status='PENDING'")->fetchColumn();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel-NAC — Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #0f3460; --accent: #e94560; --dark: #1a1a2e;
            --card-bg: #16213e; --sidebar-w: 240px;
        }
        body { background: var(--dark); color: #fff; font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; display: flex; }

        /* ---- Sidebar ---- */
        .sidebar {
            width: var(--sidebar-w); min-height: 100vh;
            background: var(--card-bg);
            border-right: 1px solid rgba(255,255,255,0.06);
            display: flex; flex-direction: column;
            position: fixed; top: 0; left: 0; z-index: 100;
        }
        .sidebar-brand { padding: 1.5rem 1.2rem; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .brand-icon { width: 36px; height: 36px; background: linear-gradient(135deg,var(--accent),var(--primary)); border-radius:8px; display:inline-flex; align-items:center; justify-content:center; margin-right:0.5rem; }
        .sidebar-brand span { font-weight: 700; font-size: 1.05rem; }
        .sidebar-nav { flex: 1; padding: 1rem 0; }
        .nav-item a { display:flex; align-items:center; gap:0.7rem; padding:0.65rem 1.2rem; color:rgba(255,255,255,0.55); text-decoration:none; font-size:0.9rem; border-left: 3px solid transparent; transition: all 0.15s; }
        .nav-item a:hover, .nav-item a.active { color:#fff; background:rgba(255,255,255,0.05); border-left-color:var(--accent); }
        .sidebar-footer { padding: 1rem 1.2rem; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.8rem; color: rgba(255,255,255,0.35); }

        /* ---- Main ---- */
        .main-content { margin-left: var(--sidebar-w); flex: 1; display: flex; flex-direction: column; }
        .topbar { background: var(--card-bg); border-bottom:1px solid rgba(255,255,255,0.06); padding: 0.9rem 1.5rem; display:flex; align-items:center; justify-content:space-between; }
        .topbar h4 { margin: 0; font-size: 1rem; font-weight: 600; }
        .content { padding: 1.5rem; }

        /* ---- Stat cards ---- */
        .stat-card { background: var(--card-bg); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding: 1.2rem 1.4rem; }
        .stat-card .icon { width:44px;height:44px; border-radius:10px; display:flex;align-items:center;justify-content:center;font-size:1.2rem; }
        .stat-card .value { font-size:1.8rem; font-weight:700; line-height:1.1; margin-top:0.5rem; }
        .stat-card .label { font-size:0.78rem; color:rgba(255,255,255,0.45); margin-top:0.15rem; }

        /* ---- Table ---- */
        .table-card { background: var(--card-bg); border:1px solid rgba(255,255,255,0.06); border-radius:12px; overflow:hidden; }
        .table-card .card-header { background: rgba(255,255,255,0.03); padding:1rem 1.3rem; border-bottom:1px solid rgba(255,255,255,0.06); font-weight:600; font-size:0.92rem; display:flex;align-items:center;gap:0.5rem; }
        table { width:100%; border-collapse:collapse; font-size:0.85rem; }
        th { background:rgba(255,255,255,0.04); color:rgba(255,255,255,0.5); font-size:0.75rem; font-weight:600; letter-spacing:.5px; text-transform:uppercase; padding:0.75rem 1rem; text-align:left; border-bottom:1px solid rgba(255,255,255,0.06); }
        td { padding: 0.7rem 1rem; border-bottom:1px solid rgba(255,255,255,0.04); color:rgba(255,255,255,0.82); vertical-align:middle; }
        tr:last-child td { border-bottom:none; }
        tr:hover td { background: rgba(255,255,255,0.02); }

        /* ---- Status badges ---- */
        .badge-allowed    { background: rgba(39,174,96,0.18); color:#27ae60; border:1px solid rgba(39,174,96,0.35); }
        .badge-blocked    { background: rgba(231,76,60,0.18);  color:#e74c3c; border:1px solid rgba(231,76,60,0.35); }
        .badge-quarantined{ background: rgba(230,126,34,0.18); color:#e67e22; border:1px solid rgba(230,126,34,0.35); }
        .badge-unknown    { background: rgba(149,165,166,0.18);color:#95a5a6; border:1px solid rgba(149,165,166,0.35); }
        .status-badge { padding:3px 9px; border-radius:20px; font-size:0.72rem; font-weight:600; }

        /* ---- Action buttons ---- */
        .btn-action { padding:3px 10px; font-size:0.75rem; border-radius:6px; border:none; cursor:pointer; transition:opacity .15s; }
        .btn-allow  { background:rgba(39,174,96,0.2);  color:#27ae60; }
        .btn-block  { background:rgba(231,76,60,0.2);  color:#e74c3c; }
        .btn-quar   { background:rgba(230,126,34,0.2); color:#e67e22; }
        .btn-logs   { background:rgba(255,255,255,0.07);color:rgba(255,255,255,0.6); }
        .btn-action:hover { opacity: 0.75; }

        /* ---- Search ---- */
        .search-box { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#fff; border-radius:8px; padding:0.45rem 0.9rem; font-size:0.85rem; width:220px; }
        .search-box:focus { outline:none; border-color:var(--accent); }
        .filter-select { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#fff; border-radius:8px; padding:0.45rem 0.7rem; font-size:0.85rem; }
        .filter-select option { background: #1a1a2e; }

        /* ---- Auto-refresh indicator ---- */
        .refresh-dot { width:8px;height:8px;border-radius:50%;background:#27ae60;display:inline-block;animation:pulse 2s infinite; margin-right:5px; }
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.3} }
    </style>
</head>
<body>

<!-- ============ SIDEBAR ============ -->
<div class="sidebar">
    <div class="sidebar-brand">
        <div class="d-flex align-items-center">
            <div class="brand-icon"><i class="fas fa-shield-halved text-white" style="font-size:.9rem"></i></div>
            <span>Sentinel-NAC</span>
        </div>
        <div style="font-size:.7rem;color:rgba(255,255,255,.3);margin-top:.3rem">Zero-Trust NAC · Lab Edition</div>
    </div>
    <nav class="sidebar-nav">
        <ul class="nav-item list-unstyled">
            <li><a href="dashboard.php" class="active"><i class="fas fa-gauge-high" style="width:16px"></i> Dashboard</a></li>
            <li><a href="dashboard.php#devices"><i class="fas fa-network-wired" style="width:16px"></i> Devices</a></li>
            <li><a href="dashboard.php#alerts"><i class="fas fa-bell" style="width:16px"></i> Alerts
                <?php if($alerts_pending>0): ?><span class="badge bg-danger ms-auto" style="font-size:.65rem"><?=$alerts_pending?></span><?php endif; ?>
            </a></li>
            <li><a href="report.php"><i class="fas fa-file-pdf" style="width:16px"></i> Reports</a></li>
            <li><a href="logout.php"><i class="fas fa-sign-out-alt" style="width:16px"></i> Logout</a></li>
        </ul>
    </nav>
    <div class="sidebar-footer">
        <i class="fas fa-user-shield me-1"></i> <?= htmlspecialchars(current_admin()) ?>
    </div>
</div>

<!-- ============ MAIN CONTENT ============ -->
<div class="main-content">
    <div class="topbar">
        <h4><i class="fas fa-gauge-high me-2" style="color:var(--accent)"></i>Network Overview</h4>
        <div class="d-flex align-items-center gap-3">
            <span style="font-size:.78rem;color:rgba(255,255,255,.4)">
                <span class="refresh-dot"></span>Auto-refreshing every 10s
            </span>
            <span style="font-size:.78rem;color:rgba(255,255,255,.35)"><?= date('D, d M Y H:i:s') ?></span>
        </div>
    </div>

    <div class="content">

        <!-- ---- Stat cards ---- -->
        <div class="row g-3 mb-4">
            <?php
            $stats = [
                ['Total Devices',  $total,      '#3498db', 'fa-network-wired'],
                ['Allowed',        $allowed,    '#27ae60', 'fa-circle-check'],
                ['Quarantined',    $quarantine, '#e67e22', 'fa-clock'],
                ['Blocked',        $blocked,    '#e74c3c', 'fa-ban'],
                ['Unknown',        $unknown,    '#95a5a6', 'fa-question-circle'],
            ];
            foreach ($stats as [$label, $val, $color, $icon]):
            ?>
            <div class="col-6 col-lg-2">
                <div class="stat-card">
                    <div class="icon" style="background:<?=$color?>22;color:<?=$color?>">
                        <i class="fas <?=$icon?>"></i>
                    </div>
                    <div class="value" style="color:<?=$color?>"><?=$val?></div>
                    <div class="label"><?=$label?></div>
                </div>
            </div>
            <?php endforeach; ?>
        </div>

        <!-- ---- Device table ---- -->
        <div class="table-card mb-4" id="devices">
            <div class="card-header justify-content-between">
                <div><i class="fas fa-network-wired me-2" style="color:var(--accent)"></i>Live Device Table</div>
                <div class="d-flex gap-2">
                    <input type="text" id="searchBox" class="search-box" placeholder="Search MAC / IP / vendor…" oninput="filterTable()">
                    <select id="statusFilter" class="filter-select" onchange="filterTable()">
                        <option value="">All Status</option>
                        <option value="ALLOWED">Allowed</option>
                        <option value="QUARANTINED">Quarantined</option>
                        <option value="BLOCKED">Blocked</option>
                        <option value="UNKNOWN">Unknown</option>
                    </select>
                </div>
            </div>
            <div style="overflow-x:auto">
                <table id="deviceTable">
                    <thead>
                        <tr>
                            <th>MAC Address</th><th>IP Address</th><th>Hostname</th>
                            <th>Vendor</th><th>OS (est.)</th>
                            <th>Status</th><th>First Seen</th><th>Last Seen</th><th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="deviceBody">
                        <?php
                        $devices = $pdo->query("SELECT * FROM devices ORDER BY last_seen DESC")->fetchAll();
                        foreach ($devices as $d):
                            $s = $d['status'];
                            $cls = strtolower("badge-$s");
                        ?>
                        <tr data-mac="<?=htmlspecialchars($d['mac_address'])?>">
                            <td><code><?=htmlspecialchars($d['mac_address'])?></code></td>
                            <td><?=htmlspecialchars($d['ip_address'] ?? '—')?></td>
                            <td><?=htmlspecialchars($d['hostname'] ?? '—')?></td>
                            <td><?=htmlspecialchars($d['vendor'] ?? '—')?></td>
                            <td><?=htmlspecialchars($d['probable_os'] ?? '—')?></td>
                            <td><span class="status-badge <?=$cls?>"><?=$s?></span></td>
                            <td><?=htmlspecialchars(str_replace(' ','&nbsp;',$d['first_seen']))?></td>
                            <td><?=htmlspecialchars(str_replace(' ','&nbsp;',$d['last_seen']))?></td>
                            <td>
                                <button class="btn-action btn-allow" onclick="doAction('allow','<?=htmlspecialchars($d['mac_address'])?>',this)">
                                    <i class="fas fa-check"></i> Allow</button>
                                <button class="btn-action btn-quar ms-1" onclick="doAction('quarantine','<?=htmlspecialchars($d['mac_address'])?>',this)">
                                    <i class="fas fa-clock"></i></button>
                                <button class="btn-action btn-block ms-1" onclick="doAction('block','<?=htmlspecialchars($d['mac_address'])?>',this)">
                                    <i class="fas fa-ban"></i></button>
                                <a class="btn-action btn-logs ms-1" href="api/logs.php?mac=<?=urlencode($d['mac_address'])?>" target="_blank">
                                    <i class="fas fa-list"></i></a>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- ---- Recent Alerts ---- -->
        <div class="table-card" id="alerts">
            <div class="card-header"><i class="fas fa-bell me-2" style="color:#e67e22"></i>Recent Alerts</div>
            <div style="overflow-x:auto">
                <table>
                    <thead><tr><th>Time</th><th>MAC</th><th>Type</th><th>Recipient</th><th>Status</th></tr></thead>
                    <tbody>
                    <?php
                    $alerts = $pdo->query("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 20")->fetchAll();
                    foreach ($alerts as $a):
                        $sc = $a['status']==='SENT' ? '#27ae60' : ($a['status']==='FAILED' ? '#e74c3c' : '#e67e22');
                    ?>
                    <tr>
                        <td><?=htmlspecialchars($a['created_at'])?></td>
                        <td><code><?=htmlspecialchars($a['mac_address'] ?? '—')?></code></td>
                        <td><?=str_replace('_',' ',$a['alert_type'])?></td>
                        <td><?=htmlspecialchars($a['recipient'])?></td>
                        <td><span class="status-badge" style="color:<?=$sc?>;background:<?=$sc?>22;border:1px solid <?=$sc?>55"><?=$a['status']?></span></td>
                    </tr>
                    <?php endforeach; ?>
                    <?php if(empty($alerts)): ?><tr><td colspan="5" style="color:rgba(255,255,255,.3);text-align:center;padding:2rem">No alerts yet</td></tr><?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
// ---- Client-side search/filter ----
function filterTable() {
    const q = document.getElementById('searchBox').value.toLowerCase();
    const sf = document.getElementById('statusFilter').value.toLowerCase();
    document.querySelectorAll('#deviceBody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        const inSearch = !q || text.includes(q);
        const badge = row.querySelector('.status-badge');
        const inFilter = !sf || (badge && badge.textContent.trim().toLowerCase() === sf);
        row.style.display = (inSearch && inFilter) ? '' : 'none';
    });
}

// ---- AJAX action handler ----
function doAction(action, mac, btn) {
    if (!confirm(`Set ${mac} to ${action.toUpperCase()}?`)) return;
    btn.disabled = true; btn.textContent = '…';
    fetch(`api/action.php?action=${action}&mac=${encodeURIComponent(mac)}`)
        .then(r => r.json())
        .then(d => {
            if (d.success) { location.reload(); }
            else { alert('Error: ' + (d.error || 'Unknown')); btn.disabled=false; }
        })
        .catch(e => { alert('Request failed'); btn.disabled=false; });
}

// ---- Auto-refresh every 10 seconds ----
setTimeout(() => location.reload(), 10000);
</script>
</body>
</html>
