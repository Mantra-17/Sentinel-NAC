import { redirect } from "next/navigation";

export default function Home() {
  // In a real app, check auth here
  redirect("/login");
}
