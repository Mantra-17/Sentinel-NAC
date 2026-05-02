const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

async function main() {
  console.log('Clearing database...');
  await prisma.deviceEvent.deleteMany({});
  await prisma.alert.deleteMany({});
  await prisma.device.deleteMany({});
  console.log('Database cleared successfully! Everything is clean now.');
}

main()
  .catch(e => console.error(e))
  .finally(async () => await prisma.$disconnect());
