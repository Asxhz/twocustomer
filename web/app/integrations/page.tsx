import { redirect } from "next/navigation";

// Integrations live in Settings (real, live connector status).
export default function Integrations() {
  redirect("/admin/settings");
}
