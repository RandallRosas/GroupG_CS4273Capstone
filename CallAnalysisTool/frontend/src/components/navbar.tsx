"use client";
import Link from "next/link";
import React, { useState, useEffect } from "react";
import Image from "next/image";
import normanPDLogo from "@/../public/norman-pd-logo.svg";
import evaluateIconBlack from "@/../public/evaluate-icon-black.svg";
import evaluateIconWhite from "@/../public/evaluate-icon-white.svg";
import reviewIconWhite from "@/../public/review-icon-white.svg";
import reviewIconBlack from "@/../public/review-icon-black.svg";
import recordsIconWhite from "@/../public/records-icon-white.svg";
import recordsIconBlack from "@/../public/records-icon-black.svg";
import helpIconWhite from "@/../public/help-icon-white.svg";
import helpIconBlack from "@/../public/help-icon-black.svg";

const Navbar = () => {
  // Create and Handle Page Title State
  const [pageTitle, setPageTitle] = useState<string>("Evaluate");
  const [isHydrated, setIsHydrated] = useState(false);

  // Handle hydration and load from localStorage,
  //This is used to persist the page title between refreshes for user experience
  useEffect(() => {
    setIsHydrated(true);
    const savedPageTitle = localStorage.getItem("pageTitle");
    if (savedPageTitle) {
      setPageTitle(savedPageTitle);
    }
  }, []);

  const handleClick = (title: string) => {
    setPageTitle(title);
    // Save to localStorage
    localStorage.setItem("pageTitle", title);
  };

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
            href="/records"
            onClick={() => handleClick("Records")}
            className={`${
              isHydrated && pageTitle === "Records"
                ? "text-[#002d62] bg-white"
                : "text-white"
            } font-roboto font-bold text-2xl rounded-[10px] px-6 py-3 flex items-center gap-4 w-full`}
          >
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center">
              <Image
                src={
                  isHydrated && pageTitle === "Records"
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
            href="/upload"
            onClick={() => handleClick("Evaluate")}
            className={`${
              isHydrated && pageTitle === "Evaluate"
                ? "text-[#002d62] bg-white"
                : "text-white"
            } font-roboto font-bold text-2xl rounded-[10px] px-6 py-3 flex items-center gap-4 w-full`}
          >
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center">
              <Image
                src={
                  isHydrated && pageTitle === "Evaluate"
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
            href="/help"
            onClick={() => handleClick("Help")}
            className={`${
              isHydrated && pageTitle === "Help"
                ? "text-[#002d62] bg-white"
                : "text-white"
            } font-roboto font-bold text-2xl rounded-[10px] px-6 py-3 flex items-center gap-4 w-full`}
          >
            <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center">
              <Image
                src={
                  isHydrated && pageTitle === "Help"
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
