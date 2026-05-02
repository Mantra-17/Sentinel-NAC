import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    console.log("Wiping all data for demo...");
    
    // Delete in order to satisfy foreign keys
    await prisma.deviceEvent.deleteMany({});
    await prisma.alert.deleteMany({});
    await prisma.device.deleteMany({});
    
    return NextResponse.json({ 
      success: true, 
      message: "DATABASE WIPED! You now have a clean slate for your real demo." 
    });
  } catch (error) {
    return NextResponse.json({ 
      success: false, 
      error: String(error) 
    }, { status: 500 });
  }
}
