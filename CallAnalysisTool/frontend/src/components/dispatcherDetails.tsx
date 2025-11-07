"use client";
import React from "react";
import Link from "next/link";
import { Dispatcher } from "@/types/dispatcher";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";

interface DispatcherDetailsProps {
  dispatcher: Dispatcher;
}

const DispatcherDetails = ({ dispatcher }: DispatcherDetailsProps) => {
  const transcriptFiles = dispatcher.files?.transcriptFiles || [];
  const audioFiles = dispatcher.files?.audioFiles || [];
  const grades = dispatcher.grades || {};

  // Compute overall grade as average of all transcript grades
  const overallGrade = transcriptFiles.length
    ? transcriptFiles.reduce((sum, filename) => {
        const fileGrades = grades[filename];
        return fileGrades ? sum + fileGrades.grade_percentage : sum;
      }, 0) / transcriptFiles.filter((f) => grades[f]).length
    : null;

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <Link
          href="/records"
          className="text-blue-500 hover:underline mb-4 inline-block"
        >
          ← Back to Records
        </Link>
        <h1 className="text-3xl font-bold mt-4">{dispatcher.name}</h1>
        {overallGrade !== null && (
          <p className="text-lg font-semibold text-blue-600 mt-1">
            Overall Dispatcher Grade: {overallGrade.toFixed(1)}%
          </p>
        )}
        <p className="text-gray-500 mt-2">Dispatcher ID: {dispatcher.id}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transcript Files */}
        <Card>
          <CardHeader>
            <CardTitle>Transcript Files</CardTitle>
            <CardDescription>{transcriptFiles.length} file(s)</CardDescription>
          </CardHeader>
          <CardContent>
            {transcriptFiles.length > 0 ? (
              <ul className="space-y-2">
                {transcriptFiles.map((filename, index) => {
                  const fileGrades = grades[filename];
                  return (
                    <li
                      key={index}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <p className="text-sm font-medium mb-2">{filename}</p>

                      {fileGrades ? (
                        <>
                          <p className="text-sm font-semibold mb-1">
                            Overall Grade: {fileGrades.grade_percentage}%
                          </p>
                          {fileGrades.detected_nature_code && (
                            <p className="text-sm mb-2">
                              Detected Nature Code:{" "}
                              {fileGrades.detected_nature_code}
                            </p>
                          )}

                          <ul className="space-y-1">
                            {Object.entries(fileGrades.per_question || {}).map(
                              ([key, question]) => (
                                <li
                                  key={key}
                                  className="flex justify-between text-sm"
                                >
                                  <span>{question.label}</span>
                                  <span
                                    className={
                                      question.status === "Asked Correctly" ||
                                      question.status === "Obvious"
                                        ? "text-green-600 font-semibold"
                                        : question.status === "Not As Scripted"
                                        ? "text-yellow-500 font-semibold"
                                        : "text-red-600 font-semibold"
                                    }
                                  >
                                    {question.status}
                                  </span>
                                </li>
                              )
                            )}
                          </ul>
                        </>
                      ) : (
                        <p className="text-gray-500">No grade available</p>
                      )}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-gray-500">No transcript files available.</p>
            )}
          </CardContent>
        </Card>

        {/* Audio Files */}
        <Card>
          <CardHeader>
            <CardTitle>Audio Files</CardTitle>
            <CardDescription>{audioFiles.length} file(s)</CardDescription>
          </CardHeader>
          <CardContent>
            {audioFiles.length > 0 ? (
              <ul className="space-y-2">
                {audioFiles.map((filename, index) => (
                  <li
                    key={index}
                    className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <p className="text-sm font-medium">{filename}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No audio files available.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DispatcherDetails;
