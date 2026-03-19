<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinel-NAC — Admin Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #0f3460;
            --accent:  #e94560;
            --dark:    #1a1a2e;
            --card-bg: #16213e;
        }
        body {
            background: var(--dark);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        .login-card {
            background: var(--card-bg);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 16px;
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 25px 60px rgba(0,0,0,0.5);
        }
        .brand-icon {
            width: 64px; height: 64px;
            background: linear-gradient(135deg, var(--accent), var(--primary));
            border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 1.2rem;
            font-size: 1.8rem; color: #fff;
        }
        h1 { color: #fff; font-size: 1.5rem; font-weight: 700; }
        .subtitle { color: rgba(255,255,255,0.45); font-size: 0.85rem; }
        .form-control {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.12);
            color: #fff;
            border-radius: 8px;
            padding: 0.7rem 1rem;
        }
        .form-control:focus {
            background: rgba(255,255,255,0.08);
            border-color: var(--accent);
            color: #fff;
            box-shadow: 0 0 0 3px rgba(233,69,96,0.2);
        }
        label { color: rgba(255,255,255,0.7); font-size: 0.85rem; }
        .btn-login {
            background: linear-gradient(135deg, var(--accent), #c0392b);
            border: none; color: #fff;
            border-radius: 8px; padding: 0.75rem;
            font-weight: 600; letter-spacing: 0.5px;
            transition: opacity 0.2s;
        }
        .btn-login:hover { opacity: 0.88; color: #fff; }
        .alert-danger { background: rgba(233,69,96,0.15); border: 1px solid var(--accent); color: #ff8fa0; }
        .badge-version {
            display: inline-block; background: rgba(255,255,255,0.08);
            color: rgba(255,255,255,0.4); font-size: 0.7rem;
            padding: 2px 8px; border-radius: 20px; margin-top: 0.4rem;
        }
    </style>
</head>
<body>
<?php
require_once 'includes/auth.php';

// Already logged in → redirect to dashboard
if (is_logged_in()) {
    header('Location: dashboard.php');
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    if (login($username, $password)) {
        header('Location: dashboard.php');
        exit;
    }
    $error = 'Invalid username or password.';
}

$msg = htmlspecialchars($_GET['msg'] ?? '');
?>
<div class="login-card text-center">
    <div class="brand-icon"><i class="fas fa-shield-halved"></i></div>
    <h1>Sentinel-NAC</h1>
    <p class="subtitle">Zero-Trust Network Access Control</p>
    <span class="badge-version">v1.0 · Lab Edition</span>

    <?php if ($error): ?>
        <div class="alert alert-danger mt-3 text-start"><i class="fas fa-exclamation-circle me-2"></i><?= htmlspecialchars($error) ?></div>
    <?php elseif ($msg): ?>
        <div class="alert alert-warning mt-3 text-start"><?= $msg ?></div>
    <?php endif; ?>

    <form method="post" class="text-start mt-4">
        <div class="mb-3">
            <label for="username"><i class="fas fa-user me-1"></i> Username</label>
            <input type="text" id="username" name="username" class="form-control mt-1"
                   placeholder="admin" required autocomplete="username">
        </div>
        <div class="mb-4">
            <label for="password"><i class="fas fa-lock me-1"></i> Password</label>
            <input type="password" id="password" name="password" class="form-control mt-1"
                   placeholder="••••••••" required autocomplete="current-password">
        </div>
        <button type="submit" class="btn btn-login w-100">
            <i class="fas fa-sign-in-alt me-2"></i>Sign In
        </button>
    </form>
    <p class="mt-4 mb-0" style="color:rgba(255,255,255,0.25);font-size:0.75rem;">
        Authorized personnel only · <a href="../docs/ethics_statement.md" style="color:rgba(255,255,255,0.35);">Ethics Policy</a>
    </p>
</div>
</body>
</html>
