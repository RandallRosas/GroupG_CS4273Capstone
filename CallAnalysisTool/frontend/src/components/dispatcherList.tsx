"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { fetchDispatchers } from "@/lib/api";
import type { DispatcherSummaryItem } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Dispatcher } from "@/types/dispatcher";

type SortField = "grade" | "name";
type SortDirection = "desc" | "asc";

type DispatcherQueryParams = {
  startDate?: string;
  endDate?: string;
};

const normalizeDispatchers = (
  backendDispatchers: DispatcherSummaryItem[]
): Dispatcher[] =>
  backendDispatchers.map((dispatcher, index) => ({
    id: dispatcher.name || `${index}`,
    name: dispatcher.name || "Unknown",
    overallGrade:
      typeof dispatcher.overallGrade === "number" ? dispatcher.overallGrade : 0,
    numRecords: dispatcher.numRecords || 0,
    numTranscripts: dispatcher.numTranscripts || 0,
    numGrades: dispatcher.numGrades || 0,
    files: {
      transcriptFiles: [],
      audioFiles: [],
    },
    grades: {},
  }));

const compareByNameAsc = (
  a: Dispatcher & { overallGrade: number },
  b: Dispatcher & { overallGrade: number }
) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" });

const sortByGradeDescending = (
  a: Dispatcher & { overallGrade: number },
  b: Dispatcher & { overallGrade: number }
) => {
  if (b.overallGrade !== a.overallGrade) {
    return b.overallGrade - a.overallGrade;
  }

  return compareByNameAsc(a, b);
};

const gradeColor = (grade: number) =>
  grade >= 80
    ? "text-green-600"
    : grade >= 50
      ? "text-yellow-500"
      : "text-red-600";

const formatDateInputValue = (date: Date): string => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const DispatcherList = () => {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [dispatchers, setDispatchers] = useState<Dispatcher[]>([]);
  const [stationGrade, setStationGrade] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [startDate, setStartDate] = useState<string>(
    searchParams.get("startDate") || ""
  );
  const [endDate, setEndDate] = useState<string>(
    searchParams.get("endDate") || ""
  );
  const [sortField, setSortField] = useState<SortField>("grade");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const loadDispatchers = async (params?: DispatcherQueryParams) => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const data = await fetchDispatchers(params);
      const backendDispatchers = Array.isArray(data?.dispatchers)
        ? data.dispatchers
        : [];

      setStationGrade(
        typeof data?.stationGrade === "number" ? data.stationGrade : null
      );
      setDispatchers(normalizeDispatchers(backendDispatchers));
    } catch (error) {
      console.error("Error loading dispatchers:", error);
      setStationGrade(null);
      setDispatchers([]);
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Unable to load dispatchers for the selected date range."
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const urlStartDate = searchParams.get("startDate") || "";
    const urlEndDate = searchParams.get("endDate") || "";

    setStartDate(urlStartDate);
    setEndDate(urlEndDate);
    loadDispatchers({
      startDate: urlStartDate || undefined,
      endDate: urlEndDate || undefined,
    });
  }, [searchParams]);

  const updateDateSearchParams = (
    nextStartDate?: string,
    nextEndDate?: string
  ) => {
    const nextParams = new URLSearchParams(searchParams.toString());

    if (nextStartDate) {
      nextParams.set("startDate", nextStartDate);
    } else {
      nextParams.delete("startDate");
    }

    if (nextEndDate) {
      nextParams.set("endDate", nextEndDate);
    } else {
      nextParams.delete("endDate");
    }

    const queryString = nextParams.toString();
    router.replace(queryString ? `${pathname}?${queryString}` : pathname);
  };

  const handleDateSearch = () => {
    updateDateSearchParams(startDate || undefined, endDate || undefined);
  };

  const handleClearDateSearch = () => {
    setStartDate("");
    setEndDate("");
    updateDateSearchParams();
  };

  const applyQuickRange = (nextStartDate: string, nextEndDate: string) => {
    setStartDate(nextStartDate);
    setEndDate(nextEndDate);
    updateDateSearchParams(nextStartDate, nextEndDate);
  };

  const handleTodaySearch = () => {
    const today = formatDateInputValue(new Date());
    applyQuickRange(today, today);
  };

  const handleLast7DaysSearch = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 6);

    applyQuickRange(
      formatDateInputValue(start),
      formatDateInputValue(end)
    );
  };

  const handleLast30DaysSearch = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 29);

    applyQuickRange(
      formatDateInputValue(start),
      formatDateInputValue(end)
    );
  };

  const handleThisYearSearch = () => {
    const end = new Date();
    const start = new Date(end.getFullYear(), 0, 1);

    applyQuickRange(
      formatDateInputValue(start),
      formatDateInputValue(end)
    );
  };

  const dispatchersWithGrades = dispatchers.map((dispatcher) => ({
    ...dispatcher,
    overallGrade:
      typeof dispatcher.overallGrade === "number" ? dispatcher.overallGrade : 0,
  }));
  const totalStationCalls = dispatchersWithGrades.reduce(
    (sum, dispatcher) => sum + (dispatcher.numGrades ?? 0),
    0
  );

  const filteredDispatchers = dispatchersWithGrades.filter((dispatcher) =>
    dispatcher.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const topDispatchers = [...dispatchersWithGrades]
    .sort(sortByGradeDescending)
    .slice(0, 3);

  const sortedDispatchers = [...filteredDispatchers].sort((a, b) => {
    if (sortField === "grade") {
      if (a.overallGrade !== b.overallGrade) {
        return sortDirection === "desc"
          ? b.overallGrade - a.overallGrade
          : a.overallGrade - b.overallGrade;
      }

      return compareByNameAsc(a, b);
    }

    return sortDirection === "asc"
      ? compareByNameAsc(a, b)
      : compareByNameAsc(b, a);
  });

  const gradeRankById = new Map(
    [...filteredDispatchers]
      .sort(sortByGradeDescending)
      .map((dispatcher, index) => [dispatcher.id, index + 1] as const)
  );

  const buildDispatcherHref = (dispatcherName: string) => {
    const query = new URLSearchParams();

    if (startDate) {
      query.set("startDate", startDate);
    }

    if (endDate) {
      query.set("endDate", endDate);
    }

    const queryString = query.toString();
    return queryString
      ? `/records/${encodeURIComponent(dispatcherName)}?${queryString}`
      : `/records/${encodeURIComponent(dispatcherName)}`;
  };

  return (
    <div className="container mx-auto max-w-7xl p-4 sm:p-6">
      <h1 className="mb-8 text-center text-3xl font-bold">
        Dispatcher Dashboard
      </h1>

      <div className="mb-6 space-y-4">
        <div className="mx-auto max-w-md">
          <Input
            type="text"
            placeholder="Search dispatchers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="mx-auto max-w-4xl rounded-xl border border-gray-200 bg-gray-50 p-4 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-center">
            <div className="flex self-stretch rounded-lg border border-gray-200 bg-white px-4 py-3 lg:min-w-50 lg:self-auto lg:items-center">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Station Grade</p>
                {stationGrade !== null ? (
                  <div>
                    <p className={`text-2xl font-bold ${gradeColor(stationGrade)}`}>
                      {stationGrade.toFixed(1)}%
                    </p>
                    <p className="text-sm text-gray-500">
                      Average of {totalStationCalls} call
                      {totalStationCalls === 1 ? "" : "s"} <br></br>from {dispatchers.length} dispatcher
                      {dispatchers.length === 1 ? "" : "s"}
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    No grades in the selected date range.
                  </p>
                )}
              </div>
            </div>

            <div className="flex flex-1 flex-col gap-4">
              <div className="flex flex-col items-center gap-4 md:flex-row md:items-end md:justify-center">
                <div className="md:w-44">
                  <label
                    htmlFor="dispatcher-start-date"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    From
                  </label>
                  <Input
                    id="dispatcher-start-date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    max={endDate || undefined}
                  />
                </div>

                <div className="md:w-44">
                  <label
                    htmlFor="dispatcher-end-date"
                    className="mb-1 block text-sm font-medium text-gray-700"
                  >
                    To
                  </label>
                  <Input
                    id="dispatcher-end-date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || undefined}
                  />
                </div>

                <div className="flex gap-2 md:pb-px">
                  <Button onClick={handleDateSearch} disabled={isLoading}>
                    {isLoading ? "Loading..." : "Date Search"}
                  </Button>
                  <Button
                    onClick={handleClearDateSearch}
                    disabled={isLoading || (!startDate && !endDate)}
                    className="bg-red-500 text-white hover:bg-red-600"
                  >
                    Reset
                  </Button>
                </div>
              </div>

              <div className="flex flex-wrap justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTodaySearch}
                  disabled={isLoading}
                >
                  Today
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLast7DaysSearch}
                  disabled={isLoading}
                >
                  Last 7 Days
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLast30DaysSearch}
                  disabled={isLoading}
                >
                  Last 30 Days
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleThisYearSearch}
                  disabled={isLoading}
                >
                  This Year
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {errorMessage && (
        <p className="mb-6 text-center text-sm text-red-600">{errorMessage}</p>
      )}
      {/* Top dispatchers, uncomment to show again */}
      {/* {topDispatchers.length > 0 && searchQuery.trim().length === 0 && !isLoading && (
        <div className="mb-10">
          <h2 className="mb-4 text-center text-xl font-bold text-blue-600 sm:text-2xl">
            Top Dispatchers
          </h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
            {topDispatchers.map((dispatcher, index) => (
              <Link
                key={dispatcher.id}
                href={buildDispatcherHref(dispatcher.id)}
              >
                <Card className="relative flex h-full cursor-pointer flex-col border-2 border-blue-500 transition-shadow hover:shadow-lg">
                  <span className="absolute top-2 right-2 mb-1 rounded-full bg-yellow-400 px-2 py-1 text-xs font-bold text-white">
                    Rank #{index + 1}
                  </span>
                  <CardContent className="flex flex-grow flex-col justify-between">
                    <CardTitle className="break-words text-lg font-semibold">
                      {dispatcher.name}
                    </CardTitle>
                    <p
                      className={`mt-2 font-semibold ${gradeColor(
                        dispatcher.overallGrade
                      )}`}
                    >
                      Overall Grade: {dispatcher.overallGrade.toFixed(1)}%
                    </p>
                    <div className="mt-2 flex justify-between text-xs text-gray-600">
                      <span>Records: {dispatcher.numRecords ?? 0}</span>
                      <span>Grades: {dispatcher.numGrades ?? 0}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )} */}

      <div className="mb-10">
        <h2 className="mb-4 text-center text-xl font-bold sm:text-2xl">
          All Dispatchers
        </h2>
        {isLoading ? (
          <p className="text-center text-gray-500">Loading dispatchers...</p>
        ) : sortedDispatchers.length === 0 ? (
          <p className="text-center text-gray-500">
            {startDate || endDate
              ? "No dispatchers found for the selected date range."
              : "No dispatchers found."}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border border-gray-300">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Rank
                  </th>
                  <th
                    className="cursor-pointer px-4 py-2 text-left text-sm font-medium"
                    onClick={() => {
                      if (sortField === "name") {
                        setSortDirection((prev) =>
                          prev === "asc" ? "desc" : "asc"
                        );
                        return;
                      }

                      setSortField("name");
                      setSortDirection("asc");
                    }}
                  >
                    <span className="inline-flex items-center gap-1">
                      <span>Dispatcher</span>
                      <span
                        className={
                          sortField === "name" ? "font-extrabold" : "font-normal"
                        }
                      >
                        {sortField === "name"
                          ? sortDirection === "desc"
                            ? "↓"
                            : "↑"
                          : "↕"}
                      </span>
                    </span>
                  </th>
                  <th
                    className="cursor-pointer px-4 py-2 text-left text-sm font-medium"
                    onClick={() => {
                      if (sortField === "grade") {
                        setSortDirection((prev) =>
                          prev === "desc" ? "asc" : "desc"
                        );
                        return;
                      }

                      setSortField("grade");
                      setSortDirection("desc");
                    }}
                  >
                    <span className="inline-flex items-center gap-1">
                      <span>Overall Grade</span>
                      <span
                        className={
                          sortField === "grade" ? "font-extrabold" : "font-normal"
                        }
                      >
                        {sortField === "grade"
                          ? sortDirection === "desc"
                            ? "↓"
                            : "↑"
                          : "↕"}
                      </span>
                    </span>
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Call Records
                  </th>
                  <th className="px-4 py-2 text-left text-sm font-medium">
                    Grades
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {sortedDispatchers.map((dispatcher) => (
                  <tr key={dispatcher.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm">
                      {gradeRankById.get(dispatcher.id)}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <Link
                        href={buildDispatcherHref(dispatcher.name)}
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
                      {dispatcher.numRecords ?? 0}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      {dispatcher.numGrades ?? 0}
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
