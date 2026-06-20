import { redirect } from "next/navigation";

// /dashboard is an alias for the brand console.
export default function Dashboard() {
  redirect("/admin");
}
