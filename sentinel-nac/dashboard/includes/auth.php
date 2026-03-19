<?php
/**
 * Sentinel-NAC: Authentication Helper (PHP)
 * File: dashboard/includes/auth.php
 * Purpose: Session-based login/logout helpers for the admin dashboard.
 */

session_start();

function is_logged_in(): bool {
    return isset($_SESSION['admin_id']) && !empty($_SESSION['admin_id']);
}

function require_login(): void {
    if (!is_logged_in()) {
        header('Location: index.php?msg=Please+log+in+first');
        exit;
    }
}

function login(string $username, string $password): bool {
    require_once __DIR__ . '/db.php';
    $pdo = get_pdo();

    $stmt = $pdo->prepare(
        "SELECT id, username, password, role FROM admins WHERE username = ? LIMIT 1"
    );
    $stmt->execute([$username]);
    $admin = $stmt->fetch();

    if ($admin && password_verify($password, $admin['password'])) {
        $_SESSION['admin_id']   = $admin['id'];
        $_SESSION['admin_user'] = $admin['username'];
        $_SESSION['admin_role'] = $admin['role'];

        // Update last_login
        $pdo->prepare("UPDATE admins SET last_login = NOW() WHERE id = ?")
            ->execute([$admin['id']]);

        // Log event
        $pdo->prepare(
            "INSERT INTO device_events
                (mac_address, event_type, actor, details)
             VALUES (NULL, 'ADMIN_ACTION', ?, 'Admin logged in')"
        )->execute([$username]);

        return true;
    }
    return false;
}

function logout(): void {
    $user = $_SESSION['admin_user'] ?? 'unknown';
    require_once __DIR__ . '/db.php';
    $pdo = get_pdo();
    $pdo->prepare(
        "INSERT INTO device_events
            (mac_address, event_type, actor, details)
         VALUES (NULL, 'ADMIN_ACTION', ?, 'Admin logged out')"
    )->execute([$user]);

    $_SESSION = [];
    session_destroy();
    header('Location: index.php');
    exit;
}

function current_admin(): string {
    return $_SESSION['admin_user'] ?? 'Unknown';
}
