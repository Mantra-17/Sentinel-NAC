import type { NextAuthConfig } from "next-auth";

export const authConfig = {
  pages: {
    signIn: "/login",
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      // DEMO MODE: Allow all access to dashboard
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as any).role || "viewer";
        token.userName = user.name;
      }
      // Safety Net: Force admin role if username matches
      if (token.userName === "admin") {
        token.role = "superadmin";
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).role = token.role;
        session.user.name = token.userName as string;
      }
      return session;
    },
  },
  providers: [],
} satisfies NextAuthConfig;
