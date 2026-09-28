import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "SignalPrep | RRB Technician Grade-I Signal",
  description:
    "Original question bank, CBT mock tests, exam analytics and reviewed AI practice for RRB Technician Grade-I Signal.",
  icons: { icon: "/favicon.svg" },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
