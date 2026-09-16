import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Smart Airport Luggage Detection & Analytics System",
  description: "AI-Powered Luggage Detection, Persistent Multi-Object Tracking, Directional Counting & Analytics for Airport Terminals.",
  keywords: ["Airport Luggage", "YOLO11", "ByteTrack", "Computer Vision", "Object Tracking", "Baggage Analytics"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen flex flex-col bg-background text-slate-100 antialiased selection:bg-brandCyan/20 selection:text-brandCyan">
        {children}
      </body>
    </html>
  );
}
