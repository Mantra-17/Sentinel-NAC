<?php
/**
 * Sentinel-NAC: Device Logs API
 * File: dashboard/api/logs.php
 * Purpose: Return event history for a specific device (JSON or HTML table).
 */

require_once dirname(__DIR__) . '/includes/auth.php';
require_once dirname(__DIR__) . '/includes/db.php';
require_login();

$mac    = strtoupper(trim($_GET['mac'] ?? ''));
$format = strtolower($_GET['format'] ?? 'html');

if (!preg_match('/^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/', $mac)) {
    http_response_code(400);
    if ($format === 'json') {
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid MAC']);
    } else {
        echo '<p style="color:red">Invalid MAC address.</p>';
    }
    exit;
}

$pdo = get_pdo();
$stmt = $pdo->prepare(
    "SELECT * FROM device_events WHERE mac_address = ? ORDER BY created_at DESC LIMIT 100"
);
$stmt->execute([$mac]);
$events = $stmt->fetchAll();

// Get device info
$dev_stmt = $pdo->prepare("SELECT * FROM devices WHERE mac_address = ? LIMIT 1");
$dev_stmt->execute([$mac]);
$device = $dev_stmt->fetch();

if ($format === 'json') {
    header('Content-Type: application/json');
    echo json_encode(['device' => $device, 'events' => $events]);
    exit;
}

// --- HTML output ---
$status_colors = [
    'ALLOWED' => '#27ae60', 'BLOCKED' => '#e74c3c',
    'QUARANTINED' => '#e67e22', 'UNKNOWN' => '#95a5a6',
];
$cur_color = $status_colors[$device['status'] ?? 'UNKNOWN'] ?? '#95a5a6';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Logs for <?=htmlspecialchars($mac)?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body{background:#1a1a2e;color:#fff;font-family:'Segoe UI',system-ui,sans-serif;padding:2rem}
        h2{font-size:1.2rem;margin-bottom:1rem}
        .card{background:#16213e;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:1.2rem;margin-bottom:1.5rem}
        .info-row{display:flex;gap:2rem;flex-wrap:wrap}
        .info-item label{font-size:.72rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.5px}
        .info-item p{margin:0;font-size:.9rem}
        table{width:100%;border-collapse:collapse;font-size:.82rem}
        th{background:rgba(255,255,255,.04);color:rgba(255,255,255,.45);font-size:.73rem;text-transform:uppercase;letter-spacing:.5px;padding:.6rem 1rem;text-align:left;border-bottom:1px solid rgba(255,255,255,.07)}
        td{padding:.6rem 1rem;border-bottom:1px solid rgba(255,255,255,.04);color:rgba(255,255,255,.8);vertical-align:middle}
        code{color:#80caff;background:rgba(128,202,255,.08);padding:2px 5px;border-radius:4px}
        .et{font-size:.72rem;background:rgba(255,255,255,.07);color:rgba(255,255,255,.6);padding:2px 7px;border-radius:10px}
    </style>
</head>
<body>
    <h2>📋 Event Log — <code><?=htmlspecialchars($mac)?></code>
        <a href="../dashboard.php" style="font-size:.8rem;color:rgba(255,255,255,.4);margin-left:1rem">← Back to Dashboard</a>
    </h2>

    <?php if ($device): ?>
    <div class="card">
        <div class="info-row">
            <div class="info-item"><label>MAC</label><p><code><?=htmlspecialchars($device['mac_address'])?></code></p></div>
            <div class="info-item"><label>IP</label><p><?=htmlspecialchars($device['ip_address'] ?? '—')?></p></div>
            <div class="info-item"><label>Vendor</label><p><?=htmlspecialchars($device['vendor'] ?? '—')?></p></div>
            <div class="info-item"><label>OS (est.)</label><p><?=htmlspecialchars($device['probable_os'] ?? '—')?></p></div>
            <div class="info-item"><label>Status</label>
                <p style="color:<?=$cur_color?>;font-weight:700"><?=htmlspecialchars($device['status'])?></p>
            </div>
            <div class="info-item"><label>First Seen</label><p><?=htmlspecialchars($device['first_seen'])?></p></div>
            <div class="info-item"><label>Last Seen</label><p><?=htmlspecialchars($device['last_seen'])?></p></div>
        </div>
    </div>
    <?php endif; ?>

    <div class="card" style="padding:0;overflow:hidden">
        <table>
            <thead><tr>
                <th>Timestamp</th><th>Event Type</th><th>Old Status</th><th>New Status</th><th>Actor</th><th>Details</th>
            </tr></thead>
            <tbody>
            <?php if (empty($events)): ?>
                <tr><td colspan="6" style="text-align:center;color:rgba(255,255,255,.3);padding:2rem">No events recorded</td></tr>
            <?php else: ?>
                <?php foreach($events as $e): ?>
                <tr>
                    <td><?=htmlspecialchars($e['created_at'])?></td>
                    <td><span class="et"><?=htmlspecialchars($e['event_type'])?></span></td>
                    <td><?=htmlspecialchars($e['old_status'] ?? '—')?></td>
                    <td><?=htmlspecialchars($e['new_status'] ?? '—')?></td>
                    <td><?=htmlspecialchars($e['actor'] ?? 'system')?></td>
                    <td><?=htmlspecialchars($e['details'] ?? '')?></td>
                </tr>
                <?php endforeach; ?>
            <?php endif; ?>
            </tbody>
        </table>
    </div>
</body>
</html>
