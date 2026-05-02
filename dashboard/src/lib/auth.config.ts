import type { NextAuthConfig } from "next-auth";

export const authConfig = {
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isOnDashboard = nextUrl.pathname.startsWith("/dashboard") || 
                           nextUrl.pathname.startsWith("/devices") || 
                           nextUrl.pathname.startsWith("/alerts") || 
                           nextUrl.pathname.startsWith("/reports") || 
                           nextUrl.pathname.startsWith("/settings");
      
      if (isOnDashboard) {
        if (isLoggedIn) return true;
        return false; // Redirect unauthenticated users to login page
      } else if (isLoggedIn) {
        return Response.redirect(new URL("/dashboard", nextUrl));
      }
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as any).role;
        token.name = user.name;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).role = token.role;
        session.user.name = token.name;
      }
      return session;
    },
  },
  providers: [],
} satisfies NextAuthConfig;
