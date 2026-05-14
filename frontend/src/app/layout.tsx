import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "next-themes";
import { QueryProvider } from "@/lib/QueryProvider";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "KDE AI | Enterprise Location Predictor",
  description: "Advanced semantic and geometric AI model to pinpoint precise real-world locations from unstructured text and tweet content.",
  openGraph: {
    title: "KDE AI | Enterprise Location Predictor",
    description: "Predict location from text using advanced semantic AI and KDE models.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "KDE AI Location Predictor",
    description: "Find the geographic location of any tweet text.",
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className={`${inter.variable} ${outfit.variable} font-sans min-h-screen bg-background`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
            <Toaster theme="dark" position="top-center" richColors closeButton />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
