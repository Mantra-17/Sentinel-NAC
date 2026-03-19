<?php
/**
 * Sentinel-NAC: Report Generator Page
 * File: dashboard/report.php
 * Purpose: Provide a UI to select date range and trigger PDF report generation.
 */
require_once 'includes/auth.php';
require_once 'includes/db.php';
require_login();

$message = '';
$report_path = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $start = $_POST['start_date'] ?? '';
    $end   = $_POST['end_date']   ?? '';

    // Validate dates
    if (!$start || !$end || $start > $end) {
        $message = '<div class="alert alert-danger">Please provide valid start and end dates.</div>';
    } else {
        // Call Python report generator via CLI
        $python    = 'python3';
        $script    = escapeshellarg(dirname(__DIR__) . '/backend/reports/report_generator.py');
        $out_dir   = dirname(__DIR__) . '/reports/output';
        $cmd = "$python $script --start " . escapeshellarg($start)
             . " --end " . escapeshellarg($end)
             . " --out " . escapeshellarg($out_dir)
             . " 2>&1";
        $output = shell_exec($cmd);

        // Parse output path from "Report saved: /path/to/file.pdf"
        if (preg_match('/Report saved:\s*(.+\.pdf)/i', $output, $m)) {
            $file = trim($m[1]);
            // Serve as download
            if (file_exists($file)) {
                header('Content-Type: application/pdf');
                header('Content-Disposition: attachment; filename="' . basename($file) . '"');
                header('Content-Length: ' . filesize($file));
                readfile($file);
                exit;
            }
        }
        $message = '<div class="alert alert-warning">Report generation output:<br><pre style="font-size:.8rem">'
                 . htmlspecialchars($output) . '</pre></div>';
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sentinel-NAC — Generate Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root{--primary:#0f3460;--accent:#e94560;--dark:#1a1a2e;--card-bg:#16213e;--sidebar-w:240px}
        body{background:var(--dark);color:#fff;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;display:flex}
        .sidebar{width:var(--sidebar-w);min-height:100vh;background:var(--card-bg);border-right:1px solid rgba(255,255,255,.06);position:fixed;top:0;left:0;z-index:100;display:flex;flex-direction:column}
        .sidebar-brand{padding:1.5rem 1.2rem;border-bottom:1px solid rgba(255,255,255,.06)}
        .brand-icon{width:36px;height:36px;background:linear-gradient(135deg,var(--accent),var(--primary));border-radius:8px;display:inline-flex;align-items:center;justify-content:center;margin-right:.5rem}
        .sidebar-nav{flex:1;padding:1rem 0}
        .nav-item a{display:flex;align-items:center;gap:.7rem;padding:.65rem 1.2rem;color:rgba(255,255,255,.55);text-decoration:none;font-size:.9rem;border-left:3px solid transparent;transition:all .15s}
        .nav-item a:hover,.nav-item a.active{color:#fff;background:rgba(255,255,255,.05);border-left-color:var(--accent)}
        .main-content{margin-left:var(--sidebar-w);flex:1;display:flex;flex-direction:column}
        .topbar{background:var(--card-bg);border-bottom:1px solid rgba(255,255,255,.06);padding:.9rem 1.5rem;display:flex;align-items:center}
        .topbar h4{margin:0;font-size:1rem;font-weight:600}
        .content{padding:1.5rem;max-width:700px}
        .report-card{background:var(--card-bg);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:2rem}
        .form-control,.form-label{color:#fff}
        .form-control{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:8px;color:#fff}
        .form-control:focus{background:rgba(255,255,255,.08);border-color:var(--accent);color:#fff;box-shadow:0 0 0 3px rgba(233,69,96,.2)}
        .btn-generate{background:linear-gradient(135deg,var(--accent),#c0392b);border:none;color:#fff;border-radius:8px;padding:.75rem 2rem;font-weight:600;transition:opacity .2s}
        .btn-generate:hover{opacity:.85;color:#fff}
        .alert-danger{background:rgba(233,69,96,.15);border:1px solid var(--accent);color:#ff8fa0}
        .alert-warning{background:rgba(230,126,34,.15);border:1px solid #e67e22;color:#f0a868}
        pre{white-space:pre-wrap;word-break:break-all;max-height:200px;overflow-y:auto;font-size:.78rem}
        .tip{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:1rem 1.2rem;font-size:.83rem;color:rgba(255,255,255,.55);margin-top:1.5rem}
    </style>
</head>
<body>
<div class="sidebar">
    <div class="sidebar-brand">
        <div class="d-flex align-items-center">
            <div class="brand-icon"><i class="fas fa-shield-halved text-white" style="font-size:.9rem"></i></div>
            <span style="font-weight:700;font-size:1.05rem">Sentinel-NAC</span>
        </div>
    </div>
    <nav class="sidebar-nav">
        <ul class="list-unstyled">
            <li class="nav-item"><a href="dashboard.php"><i class="fas fa-gauge-high" style="width:16px"></i> Dashboard</a></li>
            <li class="nav-item"><a href="report.php" class="active"><i class="fas fa-file-pdf" style="width:16px"></i> Reports</a></li>
            <li class="nav-item"><a href="logout.php"><i class="fas fa-sign-out-alt" style="width:16px"></i> Logout</a></li>
        </ul>
    </nav>
</div>

<div class="main-content">
    <div class="topbar">
        <h4><i class="fas fa-file-pdf me-2" style="color:var(--accent)"></i>Generate Audit Report</h4>
    </div>
    <div class="content">
        <?= $message ?>
        <div class="report-card">
            <h5 class="mb-1" style="color:#fff">PDF Audit Report</h5>
            <p style="color:rgba(255,255,255,.45);font-size:.85rem;margin-bottom:1.5rem">
                Select a date range to generate a downloadable PDF report containing device summary,
                status breakdown, top restricted devices, and event timeline.
            </p>
            <form method="post">
                <div class="row g-3">
                    <div class="col-6">
                        <label class="form-label" style="font-size:.83rem;color:rgba(255,255,255,.6)">Start Date</label>
                        <input type="date" name="start_date" class="form-control"
                               value="<?= date('Y-m-d', strtotime('-30 days')) ?>" required>
                    </div>
                    <div class="col-6">
                        <label class="form-label" style="font-size:.83rem;color:rgba(255,255,255,.6)">End Date</label>
                        <input type="date" name="end_date" class="form-control"
                               value="<?= date('Y-m-d') ?>" required>
                    </div>
                </div>
                <div class="mt-3">
                    <button type="submit" class="btn btn-generate">
                        <i class="fas fa-download me-2"></i>Generate &amp; Download PDF
                    </button>
                </div>
            </form>
            <div class="tip">
                <i class="fas fa-info-circle me-1"></i>
                <strong>Prerequisite:</strong> The Python backend must be installed with
                <code>reportlab</code> (<code>pip install reportlab</code>) and the database must be
                reachable from the server running PHP. See <code>docs/setup_guide.md</code> for details.
            </div>
        </div>
    </div>
</div>
</body>
</html>
