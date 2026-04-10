-- CreateEnum
CREATE TYPE "DeviceStatus" AS ENUM ('UNKNOWN', 'ALLOWED', 'BLOCKED', 'QUARANTINED');

-- CreateEnum
CREATE TYPE "AdminRole" AS ENUM ('superadmin', 'admin', 'viewer');

-- CreateEnum
CREATE TYPE "EventType" AS ENUM ('DEVICE_DISCOVERED', 'STATUS_CHANGED', 'ENFORCEMENT_STARTED', 'ENFORCEMENT_STOPPED', 'RECONNECT_BLOCKED', 'ADMIN_ACTION', 'ALERT_SENT', 'ERROR');

-- CreateEnum
CREATE TYPE "AlertType" AS ENUM ('NEW_UNKNOWN_DEVICE', 'BLOCKED_RECONNECT', 'ENFORCEMENT_FAILURE', 'SYSTEM_ERROR');

-- CreateEnum
CREATE TYPE "AlertStatus" AS ENUM ('PENDING', 'SENT', 'FAILED');

-- CreateTable
CREATE TABLE "admins" (
    "id" SERIAL NOT NULL,
    "username" VARCHAR(64) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "email" VARCHAR(128) NOT NULL,
    "role" "AdminRole" NOT NULL DEFAULT 'admin',
    "last_login" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "admins_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "devices" (
    "id" SERIAL NOT NULL,
    "mac_address" VARCHAR(17) NOT NULL,
    "ip_address" VARCHAR(45),
    "hostname" VARCHAR(128),
    "vendor" VARCHAR(128),
    "probable_os" VARCHAR(64),
    "probable_device_type" VARCHAR(64),
    "fingerprint_confidence" INTEGER DEFAULT 0,
    "status" "DeviceStatus" NOT NULL DEFAULT 'UNKNOWN',
    "first_seen" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_seen" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "notes" TEXT,

    CONSTRAINT "devices_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "device_events" (
    "id" SERIAL NOT NULL,
    "mac_address" VARCHAR(17) NOT NULL,
    "ip_address" VARCHAR(45),
    "event_type" "EventType" NOT NULL,
    "old_status" "DeviceStatus",
    "new_status" "DeviceStatus",
    "actor" VARCHAR(64),
    "details" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "device_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "alerts" (
    "id" SERIAL NOT NULL,
    "mac_address" VARCHAR(17),
    "alert_type" "AlertType" NOT NULL,
    "recipient" VARCHAR(128) NOT NULL,
    "subject" VARCHAR(255) NOT NULL,
    "body" TEXT NOT NULL,
    "sent_at" TIMESTAMP(3),
    "status" "AlertStatus" NOT NULL DEFAULT 'PENDING',
    "error_msg" VARCHAR(512),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "alerts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "system_settings" (
    "setting_key" VARCHAR(64) NOT NULL,
    "setting_value" TEXT NOT NULL,
    "description" VARCHAR(255),
    "updated_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "system_settings_pkey" PRIMARY KEY ("setting_key")
);

-- CreateIndex
CREATE UNIQUE INDEX "admins_username_key" ON "admins"("username");

-- CreateIndex
CREATE UNIQUE INDEX "devices_mac_address_key" ON "devices"("mac_address");

-- CreateIndex
CREATE INDEX "devices_status_idx" ON "devices"("status");

-- CreateIndex
CREATE INDEX "devices_last_seen_idx" ON "devices"("last_seen");

-- CreateIndex
CREATE INDEX "device_events_mac_address_idx" ON "device_events"("mac_address");

-- CreateIndex
CREATE INDEX "device_events_event_type_idx" ON "device_events"("event_type");

-- CreateIndex
CREATE INDEX "device_events_created_at_idx" ON "device_events"("created_at");

-- CreateIndex
CREATE INDEX "alerts_status_idx" ON "alerts"("status");

-- CreateIndex
CREATE INDEX "alerts_created_at_idx" ON "alerts"("created_at");

-- AddForeignKey
ALTER TABLE "device_events" ADD CONSTRAINT "device_events_mac_address_fkey" FOREIGN KEY ("mac_address") REFERENCES "devices"("mac_address") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "alerts" ADD CONSTRAINT "alerts_mac_address_fkey" FOREIGN KEY ("mac_address") REFERENCES "devices"("mac_address") ON DELETE SET NULL ON UPDATE CASCADE;
