"use server";

import { prisma } from "@/lib/prisma";
import { DeviceStatus } from "@prisma/client";
import { revalidatePath } from "next/cache";
import { auth } from "@/lib/auth";

export async function getDevices() {
  try {
    return await prisma.device.findMany({
      orderBy: {
        lastSeen: 'desc'
      }
    });
  } catch (error) {
    console.error("Error fetching devices:", error);
    return [];
  }
}

export async function updateDeviceStatus(id: number, status: DeviceStatus) {
  // Runtime input validation (TypeScript types are stripped at runtime)
  if (!Number.isInteger(id) || id < 1) {
    throw new Error("Invalid device ID: must be a positive integer.");
  }
  const validStatuses: DeviceStatus[] = ["UNKNOWN", "ALLOWED", "BLOCKED", "QUARANTINED"];
  if (!validStatuses.includes(status)) {
    throw new Error("Invalid status value.");
  }
  try {
    const session = await auth();
    const userRole = (session?.user as any)?.role;

    if (userRole !== "admin" && userRole !== "superadmin") {
      throw new Error("UNAUTHORIZED: Only administrators can modify node status.");
    }

    // If resetting to UNKNOWN, also clear any notes per user request
    const data: any = { status };
    if (status === "UNKNOWN") {
      data.notes = null;
    }

    const updated = await prisma.device.update({
      where: { id },
      data
    });
    
    revalidatePath("/dashboard");
    revalidatePath("/devices");
    return updated;
  } catch (error) {
    console.error("Error updating device status:", error);
    throw error;
  }
}

export async function deleteDevice(id: number) {
  // Runtime input validation
  if (!Number.isInteger(id) || id < 1) {
    throw new Error("Invalid device ID: must be a positive integer.");
  }
  try {
    const session = await auth();
    const userRole = (session?.user as any)?.role;

    if (userRole !== "admin" && userRole !== "superadmin") {
      throw new Error("UNAUTHORIZED: Only administrators can delete records.");
    }

    // 1. Get the device to find its MAC address
    const device = await prisma.device.findUnique({
      where: { id }
    });

    if (device) {
      // 2. Delete all events associated with this MAC
      await prisma.deviceEvent.deleteMany({
        where: { macAddress: device.macAddress }
      });

      // 3. Delete any alerts associated with this MAC
      await prisma.alert.deleteMany({
        where: { macAddress: device.macAddress }
      });

      // 4. Finally delete the device
      await prisma.device.delete({
        where: { id }
      });
    }
    
    revalidatePath("/dashboard");
    revalidatePath("/devices");
    return { success: true };
  } catch (error) {
    console.error("Error deleting device:", error);
    throw error;
  }
}
