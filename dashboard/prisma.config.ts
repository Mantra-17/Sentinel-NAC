import { defineConfig } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
    seed: "npx tsx prisma/seed.ts",
  },
  datasource: {
    url: "postgresql://neondb_owner:npg_93lthuYLKIGw@ep-hidden-glitter-aohel58q.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
  },
});
