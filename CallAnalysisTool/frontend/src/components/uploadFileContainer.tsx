"use client";
import React, { useState, useRef } from "react";
import { Dispatcher } from "@/types/dispatcher";
import { v4 as uuidv4 } from "uuid";
import { uploadFileForAnalysis, calculateGrade } from "@/lib/api";

const UploadFileContainer = () => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Define allowed audio file types
  const allowedTypes = [".zip", ".json"];

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    const validFiles: File[] = [];
    const invalidFiles: string[] = [];

    Array.from(files).forEach((file) => {
      const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
      if (allowedTypes.includes(fileExtension)) {
        validFiles.push(file);
      } else {
        invalidFiles.push(file.name);
      }
    });

    if (invalidFiles.length > 0) {
      alert(
        `The following files are not supported: ${invalidFiles.join(
          ", "
        )}\n\nOnly ${allowedTypes.join(", ")} files are allowed.`
      );
    }

    setSelectedFiles((prev) => [...prev, ...validFiles]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      alert("Please select at least one zip and json file to upload.");
      return;
    }

    setIsUploading(true);
    setUploadProgress("Processing files...");

    try {
      // Group files by dispatcher name

      if (selectedFiles[0].name.endsWith(".zip")) {
        const formData = new FormData();
        formData.append("file", selectedFiles[0]);
        console.log("Zip File");
        const response = await fetch("http://localhost:5001/api/transcribe", {
          method: "POST",
          body: formData,
        });
        const result = await response.json();
        console.log(result);
      } else {
        ////////////// JSON File Upload (OLD)
        const dispatcherMap = new Map<
          string,
          { transcriptFiles: File[]; audioFiles: File[] }
        >();

        selectedFiles.forEach((file) => {
          const filename = file.name;
          const firstUnderscoreIndex = filename.indexOf("_");
          const secondUnderscoreIndex = filename.indexOf(
            "_",
            firstUnderscoreIndex + 1
          );
          const dotIndex = filename.indexOf(".");

          if (secondUnderscoreIndex !== -1 && dotIndex !== -1) {
            const dispatcherName = filename.substring(
              secondUnderscoreIndex + 1,
              dotIndex
            );
            const fileExtension = filename.substring(dotIndex);

            // Initialize dispatcher if not exists
            if (!dispatcherMap.has(dispatcherName)) {
              dispatcherMap.set(dispatcherName, {
                transcriptFiles: [],
                audioFiles: [],
              });
            }

            const dispatcherData = dispatcherMap.get(dispatcherName)!;

            // Categorize files based on extension
            if (fileExtension === ".json") {
              dispatcherData.transcriptFiles.push(file);
            } else {
              dispatcherData.audioFiles.push(file);
            }
          }
        });

        // Helper function to update localStorage and notify listeners
        const updateDispatcherInStorage = (
          dispatcherName: string,
          filename: string,
          grade: number | undefined,
          isTranscriptFile: boolean
        ) => {
          const storedDispatchers = localStorage.getItem("dispatchers");
          const existingDispatchers: Dispatcher[] = storedDispatchers
            ? JSON.parse(storedDispatchers)
            : [];

          // Find or create dispatcher
          let dispatcher = existingDispatchers.find(
            (d) => d.name === dispatcherName
          );

          if (!dispatcher) {
            // Create new dispatcher
            dispatcher = {
              id: uuidv4(),
              name: dispatcherName,
              files: {
                transcriptFiles: [],
                audioFiles: [],
              },
              grades: {},
            };
            existingDispatchers.push(dispatcher);
          }

          // Add file if not already present
          if (isTranscriptFile) {
            if (!dispatcher.files.transcriptFiles.includes(filename)) {
              dispatcher.files.transcriptFiles.push(filename);
            }
            // Update grade
            if (!dispatcher.grades) {
              dispatcher.grades = {};
            }
            if (grade !== undefined) {
              dispatcher.grades[filename] = grade;
            }
          } else {
            if (!dispatcher.files.audioFiles.includes(filename)) {
              dispatcher.files.audioFiles.push(filename);
            }
          }

          // Store updated dispatchers array in localStorage
          localStorage.setItem(
            "dispatchers",
            JSON.stringify(existingDispatchers)
          );

          // Dispatch custom event to notify other components
          window.dispatchEvent(new CustomEvent("dispatchersUpdated"));
        };

        // Helper function to remove a file from selectedFiles by filename
        const removeFileFromList = (filename: string) => {
          setSelectedFiles((prev) =>
            prev.filter((file) => file.name !== filename)
          );
        };

        // First, add all audio files to their dispatchers and remove them from the list
        dispatcherMap.forEach((files, dispatcherName) => {
          files.audioFiles.forEach((audioFile) => {
            updateDispatcherInStorage(
              dispatcherName,
              audioFile.name,
              undefined,
              false
            );
            // Remove audio file from selected files list immediately
            removeFileFromList(audioFile.name);
          });
        });

        // Upload JSON files to API and get grades
        let successCount = 0;
        let errorCount = 0;
        const errors: string[] = [];

        for (const [dispatcherName, files] of dispatcherMap.entries()) {
          // Process each JSON file
          for (const jsonFile of files.transcriptFiles) {
            setUploadProgress(`Analyzing ${jsonFile.name}...`);

            try {
              const apiResponse = await uploadFileForAnalysis(jsonFile);
              const grade = calculateGrade(apiResponse);

              // Update localStorage immediately after each file is graded
              updateDispatcherInStorage(
                dispatcherName,
                jsonFile.name,
                grade,
                true
              );

              // Remove file from selected files list after successful grading
              removeFileFromList(jsonFile.name);

              successCount++;
            } catch (error) {
              errorCount++;
              const errorMessage =
                error instanceof Error ? error.message : "Unknown error";
              errors.push(`${jsonFile.name}: ${errorMessage}`);
              console.error(`Error analyzing ${jsonFile.name}:`, error);

              // Still add the file even if grading failed
              updateDispatcherInStorage(
                dispatcherName,
                jsonFile.name,
                undefined,
                true
              );

              // Remove file from selected files list even if grading failed
              removeFileFromList(jsonFile.name);
            }
          }
        }

        // Show appropriate message based on results
        if (successCount === 0 && errorCount > 0) {
          // All files failed
          alert(
            `Failed to analyze any files.\n\nErrors:\n${errors
              .slice(0, 5)
              .join("\n")}${
              errors.length > 5 ? `\n...and ${errors.length - 5} more` : ""
            }\n\nFiles were saved but no grades were calculated.`
          );
        } else if (errorCount > 0) {
          // Some files succeeded, some failed
          alert(
            `Successfully analyzed ${successCount} file(s), but ${errorCount} file(s) failed.\n\nFailed files:\n${errors
              .slice(0, 3)
              .join("\n")}${
              errors.length > 3 ? `\n...and ${errors.length - 3} more` : ""
            }`
          );
        } else {
          // All files succeeded
          alert(`Successfully stored dispatcher(s) with files and grades!`);
        }
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert(
        `Error uploading files: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setIsUploading(false);
      setUploadProgress("");
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold mb-2">
          Upload Zip and JSON Files
        </h2>
      </div>

      {/* Drag and Drop Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className="space-y-2">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="text-lg font-medium text-gray-700">
            Drop zip and json files here, or click to browse
          </p>
          <p className="text-sm text-gray-500">Zip and JSON files only</p>
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".zip,.json"
        onChange={(e) => handleFileSelect(e.target.files)}
        className="hidden"
      />

      {/* Selected Files List */}
      {selectedFiles.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-3">
            Selected Files ({selectedFiles.length})
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex-1">
                  <p className="font-medium text-sm">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                  </p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-red-500 hover:text-red-700 ml-2"
                >
                  <svg
                    className="h-5 w-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700 font-medium">{uploadProgress}</p>
        </div>
      )}

      {/* Upload Button */}
      <div className="mt-6">
        <button
          onClick={handleUpload}
          disabled={selectedFiles.length === 0 || isUploading}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
            selectedFiles.length === 0 || isUploading
              ? "bg-gray-300 text-gray-500 cursor-not-allowed"
              : "bg-blue-500 text-white hover:bg-blue-600"
          }`}
        >
          {isUploading
            ? "Uploading and Analyzing..."
            : `Upload${
                selectedFiles.length > 0
                  ? ` ${selectedFiles.length} file(s)`
                  : ""
              }`}
        </button>
      </div>
    </div>
  );
};

export default UploadFileContainer;
