import "./globals.css";
export const metadata = { title: "ReelMind", description: "AI Reel Growth & Editing Agent" };
export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}