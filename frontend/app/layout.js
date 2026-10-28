import localFont from "next/font/local";
import "./globals.css";
import ClientLayout from "./ClientLayout";

// The Nix build copies InterVariable.ttf into app/fonts. For local development,
// copy it from the Inter font package, or run `nix develop`, which does it.
const inter = localFont({ src: "./fonts/InterVariable.ttf" });

export const metadata = {
    applicationName: "Gangway",
    appleWebApp: {
        capable: true,
        statusBarStyle: "default",
        title: "Gangway",
    },
    title: "GANGWAY Control",
    description: "LED Controller Interface",
    formatDetection: {
        telephone: false,
    },
    icons: {
        shortcut: "/favicon.ico",
        apple: "/icons/apple-touch-icon.png",
        icon: [
            { url: "/favicon.svg", type: "image/svg+xml" },
            { url: "/favicon.png", type: "image/png" },
            { url: "/favicon.ico" },
        ],
    },
    manifest: "/manifest.json",
};

export const viewport = {
    themeColor: "#000000",
    width: "device-width",
    initialScale: 1,
    maximumScale: 1,
    userScalable: false,
    viewportFit: "cover",
};

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <ClientLayout>{children}</ClientLayout>
            </body>
        </html>
    );
}
