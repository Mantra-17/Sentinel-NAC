<?php
/**
 * Sentinel-NAC: Device Action API
 * File: dashboard/api/action.php
 * Purpose: Handle allow / block / quarantine actions from the dashboard.
 * Returns JSON.
 */

header('Content-Type: application/json');
require_once dirname(__DIR__) . '/includes/auth.php';
require_once dirname(__DIR__) . '/includes/db.php';

require_login();

$action = strtolower(trim($_GET['action'] ?? ''));
$mac    = strtoupper(trim($_GET['mac']    ?? ''));

$valid_actions = ['allow', 'block', 'quarantine'];
if (!in_array($action, $valid_actions, true)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid action.']);
    exit;
}

if (!preg_match('/^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/', $mac)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Invalid MAC address.']);
    exit;
}

$status_map = [
    'allow'      => 'ALLOWED',
    'block'      => 'BLOCKED',
    'quarantine' => 'QUARANTINED',
];

$new_status = $status_map[$action];
$pdo        = get_pdo();
$admin      = current_admin();

try {
    // Get current device
    $stmt = $pdo->prepare("SELECT id, status FROM devices WHERE mac_address = ?");
    $stmt->execute([$mac]);
    $device = $stmt->fetch();

    if (!$device) {
        echo json_encode(['success' => false, 'error' => 'Device not found.']);
        exit;
    }

    $old_status = $device['status'];

    // Update status
    $pdo->prepare("UPDATE devices SET status = ? WHERE mac_address = ?")
        ->execute([$new_status, $mac]);

    // Log event
    $pdo->prepare(
        "INSERT INTO device_events
            (mac_address, event_type, old_status, new_status, actor, details)
         VALUES (?, 'ADMIN_ACTION', ?, ?, ?, ?)"
    )->execute([
        $mac, $old_status, $new_status, $admin,
        "Admin set status to $new_status",
    ]);

    echo json_encode([
        'success'    => true,
        'mac'        => $mac,
        'new_status' => $new_status,
        'actor'      => $admin,
    ]);

} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Database error.']);
}
