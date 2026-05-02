/**
 * Sentinel-NAC: In-memory rate limiter for login endpoint protection.
 * Blocks IPs after MAX_ATTEMPTS failed requests within WINDOW_MS.
 * Resets on server restart (acceptable for this use case).
 */

const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000; // 15 minutes

interface RateLimitEntry {
  count: number;
  resetAt: number;
}

const attempts = new Map<string, RateLimitEntry>();

/**
 * Check if an IP is rate-limited.
 * Returns { limited: true, retryAfterMs } if blocked, { limited: false } otherwise.
 */
export function checkRateLimit(ip: string): {
  limited: boolean;
  retryAfterMs?: number;
} {
  const now = Date.now();
  const entry = attempts.get(ip);

  if (!entry || now > entry.resetAt) {
    // First attempt or window expired — reset
    attempts.set(ip, { count: 1, resetAt: now + WINDOW_MS });
    return { limited: false };
  }

  if (entry.count >= MAX_ATTEMPTS) {
    return { limited: true, retryAfterMs: entry.resetAt - now };
  }

  entry.count++;
  return { limited: false };
}

/**
 * Reset the rate limit for an IP (call on successful login).
 */
export function resetRateLimit(ip: string): void {
  attempts.delete(ip);
}

// Periodically clean up expired entries to prevent memory leaks
setInterval(() => {
  const now = Date.now();
  for (const [ip, entry] of attempts) {
    if (now > entry.resetAt) {
      attempts.delete(ip);
    }
  }
}, 60 * 1000); // Every 60 seconds
