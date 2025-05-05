import type { Metadata } from "next";
import "../styles/index.scss";
import Header from "@/components/header/header";
import Footer from "@/components/footer/footer";
import { ToastContainer } from "react-toastify";

export const metadata: Metadata = {
  title: "Record Linker",
  description: "",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
        <ToastContainer position="bottom-left" />
      </body>
    </html>
  );
}
