"use client";
import React, { useState } from "react";
import ProtocolBook from "@/components/ProtocolBook";

export default function Help() {
  const [activeTab, setActiveTab] = useState<"settings" | "ems" | "other">(
    "settings"
  );

  const [openSettingsItem, setOpenSettingsItem] = useState<string | null>(null);
  const [openOtherItem, setOpenOtherItem] = useState<string | null>(null);

  const settingsItems = [
    {
      id: "profile",
      title: "Profile",
      content: "Update your name, email, and contact information.",
    },
    {
      id: "notifications",
      title: "Notifications",
      content: "Turn on/off alerts for call updates and grading notifications.",
    },
    {
      id: "theme",
      title: "Theme",
      content: "Switch between light and dark mode to match your preference.",
    },
    {
      id: "privacy",
      title: "Privacy",
      content: "Control who can see your activity and data sharing settings.",
    },
    {
      id: "integrations",
      title: "Integrations",
      content:
        "Connect external tools such as calendars or EMS reporting software.",
    },
  ];

  const otherItems = [
    {
      id: "faq",
      title: "FAQ: Common Issues",
      content:
        "Answers to frequently asked questions about call grading, logging, and EMS protocols.",
    },
    {
      id: "getting-started",
      title: "Getting Started",
      content:
        "Step-by-step instructions for new users to set up their account and start using the app efficiently.",
    },
    {
      id: "troubleshooting",
      title: "Troubleshooting",
      content:
        "Tips for solving common technical issues, including login problems, slow loading, or unexpected errors.",
    },
    {
      id: "contact",
      title: "Contact Support",
      content:
        "How to reach the support team for further assistance, including email, chat, and phone options.",
    },
  ];

  const toggleItem = (id: string, type: "settings" | "other") => {
    if (type === "settings") {
      setOpenSettingsItem(openSettingsItem === id ? null : id);
    } else {
      setOpenOtherItem(openOtherItem === id ? null : id);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8 max-w-6xl mx-auto">
      <h1 className="text-4xl font-extrabold mb-6" style={{ color: "#002d62" }}>
        Help Center
      </h1>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b border-gray-300">
        <button
          className={`px-4 py-2 font-semibold ${
            activeTab === "settings"
              ? "border-b-4 border-blue-600 text-blue-600"
              : "text-gray-600"
          }`}
          onClick={() => setActiveTab("settings")}
        >
          Settings
        </button>
        <button
          className={`px-4 py-2 font-semibold ${
            activeTab === "ems"
              ? "border-b-4 border-blue-600 text-blue-600"
              : "text-gray-600"
          }`}
          onClick={() => setActiveTab("ems")}
        >
          EMS Protocol Book
        </button>
        <button
          className={`px-4 py-2 font-semibold ${
            activeTab === "other"
              ? "border-b-4 border-blue-600 text-blue-600"
              : "text-gray-600"
          }`}
          onClick={() => setActiveTab("other")}
        >
          Other Help
        </button>
      </div>

      {/* Tab content */}
      <div>
        {/* Settings Tab */}
        {activeTab === "settings" && (
          <div className="space-y-2">
            {settingsItems.map((item) => (
              <div
                key={item.id}
                className="border rounded-md shadow-sm bg-white"
              >
                <button
                  className="w-full text-left px-4 py-2 font-semibold flex justify-between items-center hover:bg-gray-100"
                  onClick={() => toggleItem(item.id, "settings")}
                >
                  {item.title}
                  <span>{openSettingsItem === item.id ? "▼" : "▶"}</span>
                </button>
                {openSettingsItem === item.id && (
                  <div className="px-4 py-2 text-gray-700 border-t">
                    {item.content}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* EMS Protocol Book Tab */}
        {activeTab === "ems" && <ProtocolBook />}

        {/* Other Help Tab */}
        {activeTab === "other" && (
          <div className="space-y-2">
            {otherItems.map((item) => (
              <div
                key={item.id}
                className="border rounded-md shadow-sm bg-white"
              >
                <button
                  className="w-full text-left px-4 py-2 font-semibold flex justify-between items-center hover:bg-gray-100"
                  onClick={() => toggleItem(item.id, "other")}
                >
                  {item.title}
                  <span>{openOtherItem === item.id ? "▼" : "▶"}</span>
                </button>
                {openOtherItem === item.id && (
                  <div className="px-4 py-2 text-gray-700 border-t">
                    {item.content}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
