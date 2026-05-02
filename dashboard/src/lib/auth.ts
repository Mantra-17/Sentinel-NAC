import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import { prisma } from "./prisma";
import { authConfig } from "./auth.config";

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers: [
    Credentials({
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null;
        
        const admin = await prisma.admin.findUnique({
          where: { username: credentials.username as string },
        });
        
        if (!admin) return null;
        
        const valid = await bcrypt.compare(
          credentials.password as string,
          admin.password
        );
        
        if (!valid) return null;
        
        await prisma.admin.update({
          where: { id: admin.id },
          data: { lastLogin: new Date() },
        });

        return { 
          id: String(admin.id), 
          name: admin.username, 
          email: admin.email,
          role: admin.role as string
        };
      },
    }),
  ],
  session: { strategy: "jwt" },
  secret: process.env.AUTH_SECRET,
});
