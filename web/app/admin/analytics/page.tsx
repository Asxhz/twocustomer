import { redirect } from "next/navigation";

// Analytics is merged into the dashboard.
export default function Analytics() {
  redirect("/admin");
}
