"use client";
import Link from "next/link";
import React from "react";
import Image from "next/image";
import { usePathname } from "next/navigation";
import normanPDLogo from "@/../public/norman-pd-logo.svg";
import evaluateIconBlack from "@/../public/evaluate-icon-black.svg";
import evaluateIconWhite from "@/../public/evaluate-icon-white.svg";
import recordsIconWhite from "@/../public/records-icon-white.svg";
import recordsIconBlack from "@/../public/records-icon-black.svg";
import helpIconWhite from "@/../public/help-icon-white.svg";
import helpIconBlack from "@/../public/help-icon-black.svg";

const Navbar = () => {
  const pathname = usePathname();

  const activePage =
    pathname === "/evaluate"
      ? "Evaluate"
      : pathname.startsWith("/records")
        ? "Records"
        : pathname.startsWith("/help")
          ? "Help"
          : "";

  // Create NavBar Component
  return (
    <>
      <div className="w-[180px] sm:w-[220px] md:w-[260px] lg:w-[290px] min-h-screen bg-[#002d62] flex flex-col sticky top-0">
        {/* Norman PD Logo at the top */}
        <div className="flex justify-center pt-8 pb-8">
          <Link href="/records">
            <Image src={normanPDLogo} alt="logo" width={180} height={180} />
          </Link>
        </div>

        {/* Navigation Links */}
        <div className="flex flex-col gap-8 items-center px-6">
          <Link
            href="/evaluate"
            className={`${
              activePage === "Evaluate"
                ? "text-[#002d62] bg-white"
                : "text-white"
            } font-roboto font-bold text-2xl rounded-[10px] px-6 py-3 flex items-center gap-4 w-full`}
          >
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center">
              <Image
                src={
                  activePage === "Evaluate"
                    ? evaluateIconBlack
                    : evaluateIconWhite
                }
                alt="evaluate"
                width={40}
                height={40}
              />
            </div>
            <span className="flex-1 text-left">Evaluate</span>
          </Link>

          <Link
            href="/records"
            className={`${
              activePage === "Records"
                ? "text-[#002d62] bg-white"
                : "text-white"
            } font-roboto font-bold text-2xl rounded-[10px] px-6 py-3 flex items-center gap-4 w-full`}
          >
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center">
              <Image
                src={
                  activePage === "Records"
                    ? recordsIconBlack
                    : recordsIconWhite
                }
                alt="records"
                width={40}
                height={40}
              />
            </div>
            <span className="flex-1 text-left">Records</span>
          </Link>

          <Link
            href="/help"
            className={`${
              activePage === "Help"
                ? "text-[#002d62] bg-white"
                : "text-white"
            } font-roboto font-bold text-2xl rounded-[10px] px-6 py-3 flex items-center gap-4 w-full`}
          >
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center">
              <Image
                src={
                  activePage === "Help"
                    ? helpIconBlack
                    : helpIconWhite
                }
                alt="help"
                width={28}
                height={40}
              />
            </div>
            <span className="flex-1 text-left">Help</span>
          </Link>
        </div>
      </div>
    </>
  );
};

export default Navbar;
