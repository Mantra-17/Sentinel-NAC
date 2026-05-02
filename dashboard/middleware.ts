import NextAuth from "next-auth";
import { authConfig } from "./src/lib/auth.config";
import { NextResponse } from "next/server";
import { checkRateLimit } from "./src/lib/rate-limit";

const { auth } = NextAuth(authConfig);

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isLoginPage = req.nextUrl.pathname.startsWith("/login");
  const isApiAuthRoute = req.nextUrl.pathname.startsWith("/api/auth");

  // Rate limit login attempts (brute-force protection)
  if (isApiAuthRoute && req.method === "POST") {
    const ip =
      req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
      req.headers.get("x-real-ip") ||
      "unknown";
    const { limited, retryAfterMs } = checkRateLimit(ip);
    if (limited) {
      return new NextResponse(
        JSON.stringify({
          error: "Too many login attempts. Please try again later.",
        }),
        {
          status: 429,
          headers: {
            "Content-Type": "application/json",
            "Retry-After": String(Math.ceil((retryAfterMs || 0) / 1000)),
          },
        }
      );
    }
  }

  // NextAuth will handle the redirect logic based on authConfig.callbacks.authorized
  return;
});

export const config = {
  matcher: ["/((?!api/(?!auth)|_next/static|_next/image|favicon.ico).*)"],
};
