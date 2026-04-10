import { PrismaClient, DeviceStatus, AdminRole } from "@prisma/client";
import { PrismaPg } from "@prisma/adapter-pg";
import pg from "pg";
import bcrypt from "bcryptjs";
import * as dotenv from "dotenv";

dotenv.config();

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  throw new Error("DATABASE_URL is not set");
}
const pool = new pg.Pool({ connectionString });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

async function main() {
  const hashedPassword = await bcrypt.hash("password123", 10);

  // Upsert Superadmin
  const superadmin = await prisma.admin.upsert({
    where: { username: "admin" },
    update: { role: "superadmin" },
    create: {
      username: "admin",
      password: hashedPassword,
      email: "admin@sentinel.local",
      role: "superadmin",
    },
  });

  // Upsert Simple User
  const simpleUser = await prisma.admin.upsert({
    where: { username: "user" },
    update: { role: "viewer" },
    create: {
      username: "user",
      password: hashedPassword,
      email: "user@sentinel.local",
      role: "viewer",
    },
  });

  console.log("Admin users created/updated:", superadmin.username, simpleUser.username);

  // Create Mock Devices
  const devices = [
    {
      macAddress: "00:1A:2B:3C:4D:5E",
      ipAddress: "192.168.1.10",
      hostname: "WIN-WORKSTATION-01",
      vendor: "Dell Inc.",
      probableOs: "Windows 11",
      probableDeviceType: "Workstation",
      status: DeviceStatus.ALLOWED,
      fingerprintConfidence: 95,
    },
    {
      macAddress: "AA:BB:CC:DD:EE:FF",
      ipAddress: "192.168.1.25",
      hostname: "MACBOOK-PRO-M3",
      vendor: "Apple Inc.",
      probableOs: "macOS Sequoia",
      probableDeviceType: "Laptop",
      status: DeviceStatus.QUARANTINED,
      fingerprintConfidence: 88,
    },
    {
      macAddress: "DE:AD:BE:EF:CA:FE",
      ipAddress: "192.168.1.50",
      hostname: "IOT-SMART-PLUG",
      vendor: "TP-Link",
      probableOs: "Embedded Linux",
      probableDeviceType: "IoT Device",
      status: DeviceStatus.BLOCKED,
      fingerprintConfidence: 100,
    },
    {
      macAddress: "FE:ED:FA:CE:B0:0B",
      ipAddress: "10.0.0.102",
      hostname: "SERVER-APP-01",
      vendor: "HP Enterprise",
      probableOs: "Ubuntu 24.04",
      probableDeviceType: "Server",
      status: DeviceStatus.QUARANTINED,
      fingerprintConfidence: 92,
    },
  ];

  for (const device of devices) {
    await prisma.device.upsert({
      where: { macAddress: device.macAddress },
      update: {},
      create: device,
    });
  }

  console.log("Mock devices created/updated.");

  // Create Mock Events
  const events = [
    {
      macAddress: "00:1A:2B:3C:4D:5E",
      ipAddress: "192.168.1.10",
      eventType: "DEVICE_DISCOVERED",
      details: "New workstation detected on VLAN 10",
      actor: "SYSTEM",
    },
    {
      macAddress: "AA:BB:CC:DD:EE:FF",
      ipAddress: "192.168.1.25",
      eventType: "ALERT_SENT",
      details: "Alert sent to admin@sentinel.local",
      actor: "ALERT_ENGINE",
    },
    {
      macAddress: "DE:AD:BE:EF:CA:FE",
      ipAddress: "192.168.1.50",
      eventType: "ENFORCEMENT_STARTED",
      details: "Port isolation triggered via SNMP",
      actor: "ENFORCER",
    },
  ];

  for (const event of events) {
    await prisma.deviceEvent.create({
      data: {
        ...event,
        eventType: event.eventType as any,
      },
    });
  }

  // Create Mock Alerts
  const alerts = [
    {
      macAddress: "AA:BB:CC:DD:EE:FF",
      alertType: "NEW_UNKNOWN_DEVICE",
      recipient: "admin@sentinel.local",
      subject: "CRITICAL: Unknown Device AA:BB:CC:DD:EE:FF",
      body: "An unknown device has joined the network. Immediate validation required.",
      status: "PENDING",
    },
  ];

  for (const alert of alerts) {
    await prisma.alert.create({
      data: {
        ...alert,
        alertType: alert.alertType as any,
        status: alert.status as any,
      },
    });
  }

  console.log("Mock events and alerts created.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
