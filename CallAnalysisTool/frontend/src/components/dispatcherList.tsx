"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Dispatcher } from "@/types/dispatcher";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { seedDispatchers } from "@/utils/seedDispatchers";

const DispatcherList = () => {
  const [dispatchers, setDispatchers] = useState<Dispatcher[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortDescending, setSortDescending] = useState(true);

  // load all dispatchers
  const loadDispatchers = () => {
    seedDispatchers(); // ensure seed exists
    const storedDispatchers: Dispatcher[] =
      JSON.parse(localStorage.getItem("dispatchers") || "[]") || [];
    setDispatchers(storedDispatchers);
  };

  useEffect(() => {
    loadDispatchers();
    const handleUpdate = () => loadDispatchers();
    window.addEventListener("dispatchersUpdated", handleUpdate);
    return () => window.removeEventListener("dispatchersUpdated", handleUpdate);
  }, []);

  // Compute overall grade
  const dispatchersWithGrades = dispatchers.map((dispatcher) => {
    const transcriptFiles = dispatcher.files?.transcriptFiles || [];
    const grades = dispatcher.grades || {};
    const gradedFiles = transcriptFiles.filter((file) => grades[file]);
    const overallGrade =
      gradedFiles.length > 0
        ? gradedFiles.reduce(
            (sum, file) => sum + grades[file].grade_percentage,
            0
          ) / gradedFiles.length
        : 0;
    return { ...dispatcher, overallGrade };
  });

  //  search implemented
  const filteredDispatchers = dispatchersWithGrades.filter((d) =>
    d.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // sort dispatchers by overall grade
  const sortedDispatchers = [...filteredDispatchers].sort((a, b) =>
    sortDescending
      ? b.overallGrade - a.overallGrade
      : a.overallGrade - b.overallGrade
  );

  const topDispatchers = sortedDispatchers.slice(0, 3);
  const otherDispatchers = sortedDispatchers.slice(3);

  // get grade color
  const gradeColor = (grade: number) =>
    grade >= 80
      ? "text-green-600"
      : grade >= 50
      ? "text-yellow-500"
      : "text-red-600";

  return (
    <div className="container mx-auto p-4 sm:p-6 max-w-7xl">
      <h1 className="text-3xl font-bold text-center mb-8">
        Dispatcher Dashboard
      </h1>

      {/* Search Bar */}
      {dispatchers.length > 0 && (
        <div className="mb-6 max-w-md mx-auto">
          <input
            type="text"
            placeholder="Search dispatchers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Top Dispatchers */}
      {topDispatchers.length > 0 && (
        <div className="mb-10">
          <h2 className="text-xl sm:text-2xl font-bold mb-4 text-center text-blue-600">
            Top Dispatchers
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {topDispatchers.map((dispatcher, index) => (
              <Link key={dispatcher.id} href={`/records/${dispatcher.id}`}>
                <Card className="cursor-pointer hover:shadow-lg transition-shadow h-full flex flex-col relative border-blue-500 border-2">
                  <span className="absolute top-2 left-2 bg-yellow-400 text-white text-xs font-bold px-2 py-1 rounded-full">
                    Rank #{index + 1}
                  </span>
                  <CardHeader className="flex-shrink-0">
                    <CardTitle className="text-lg font-semibold break-words">
                      {dispatcher.name}
                    </CardTitle>
                    <CardDescription className="text-xs truncate">
                      ID: {dispatcher.id.substring(0, 8)}...
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-grow flex flex-col justify-between">
                    <p
                      className={`font-semibold mt-2 ${gradeColor(
                        dispatcher.overallGrade
                      )}`}
                    >
                      Overall Grade: {dispatcher.overallGrade.toFixed(1)}%
                    </p>
                    <div className="flex justify-between mt-2 text-xs text-gray-600">
                      <span>
                        Transcript: {dispatcher.files.transcriptFiles.length}
                      </span>
                      <span>Audio: {dispatcher.files.audioFiles.length}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* All Dispatchers Table */}
      <div className="mb-10">
        <h2 className="text-xl sm:text-2xl font-bold mb-4 text-center">
          All Dispatchers
        </h2>
        {otherDispatchers.length === 0 ? (
          <p className="text-gray-500 text-center">
            No other dispatchers found.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full border border-gray-300 divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Rank
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Dispatcher
                  </th>
                  <th
                    className="px-4 py-2 text-left text-sm font-medium cursor-pointer"
                    onClick={() => setSortDescending(!sortDescending)}
                  >
                    Overall Grade {sortDescending ? "↓" : "↑"}
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Transcript Files
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Audio Files
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {otherDispatchers.map((dispatcher, index) => (
                  <tr key={dispatcher.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm">{index + 4}</td>
                    <td className="px-4 py-2 text-sm">
                      <Link
                        href={`/records/${dispatcher.id}`}
                        className="text-blue-600 hover:underline"
                      >
                        {dispatcher.name}
                      </Link>
                    </td>
                    <td
                      className={`px-4 py-2 text-sm font-semibold ${gradeColor(
                        dispatcher.overallGrade
                      )}`}
                    >
                      {dispatcher.overallGrade.toFixed(1)}%
                    </td>
                    <td className="px-4 py-2 text-sm">
                      {dispatcher.files.transcriptFiles.length}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      {dispatcher.files.audioFiles.length}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DispatcherList;
