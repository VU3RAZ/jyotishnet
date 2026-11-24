// SPDX-License-Identifier: AGPL-3.0-or-later
import type { Metadata } from "next";
import "@fontsource/hind/400.css";
import "@fontsource/hind/500.css";
import "@fontsource/hind/600.css";
import "@fontsource/martel/400.css";
import "@fontsource/martel/700.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "JyotishNet workbench",
  description: "Vedic astrology workbench: charts, vargas, dashas and birth-time rectification.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
