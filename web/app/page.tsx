import { redirect } from "next/navigation";

// No marketing landing. this is an app. Send everyone to the dashboard; the
// proxy routes unauthenticated users to sign-in and unfinished admins to setup.
export default function Home() {
  redirect("/admin");
}
