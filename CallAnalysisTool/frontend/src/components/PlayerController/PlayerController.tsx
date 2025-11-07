"use client";
import styles from "./PlayerController.module.css";
import { AudioPlayer } from "../AudioPlayer/AudioPlayer";
import { useEffect, useState } from "react";
import { TranscriptPlayer } from "../TranscriptPlayer/TranscriptPlayer";

interface PlayerControllerProps {
  transcriptionId?: string;
}

export default function PlayerController({
  transcriptionId,
}: PlayerControllerProps) {
  // states
  const [fileName, setFileName] = useState("N/A");
  const [fileURL, setFileURL] = useState<string | null>(null);
  const [transcription, setTranscription] = useState("");
  const [currentTime, setCurrentTime] = useState(0);
  const [transcriptionLoaded, setTranscriptionLoaded] = useState(false);

  // Load transcription when transcriptionId is provided
  useEffect(() => {
    if (transcriptionId) {
      // Reset state when loading new transcription
      setTranscriptionLoaded(false);
      setTranscription("");

      // Fetch transcription from the backend API
      fetch(`http://localhost:5001/api/transcriptions/${transcriptionId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Failed to fetch transcription`);
          }
          return response.json();
        })
        .then((data) => {
          if (data.success && data.data) {
            setTranscription(data.data);
            setTranscriptionLoaded(true);
            if (data.audio_file) {
              setFileURL(`http://localhost:5001/api/output/${data.audio_file}`);
              const audioFileName =
                data.audio_file.split("/").pop() || data.filename;
              if (audioFileName.endsWith(".json")) {
                const audioFileFromData = data.data.audio_file;
                if (audioFileFromData) {
                  setFileName(
                    audioFileFromData.split("/").pop() ||
                      audioFileName.replace(".json", ".wav")
                  );
                } else {
                  setFileName(audioFileName.replace(".json", ".wav"));
                }
              } else {
                setFileName(audioFileName);
              }
            } else if (data.filename) {
              // Fallback: use filename but ensure it's not .json
              const name = data.filename.endsWith(".json")
                ? data.filename.replace(".json", ".wav")
                : data.filename;
              setFileName(name);
            }
          }
        })
        .catch((error) => {
          console.error("Error loading transcription:", error);
          setTranscriptionLoaded(false);
        });
    }
  }, [transcriptionId]);

  // handlers
  const handleGetFile = (name: string) => {
    setFileName(name);
    setTranscriptionLoaded(false); // Reset when manually selecting a file
  };

  const handleGetURL = (url: string) => {
    setFileURL(url);
  };

  // extracting dispatcher name from file name
  const match = fileName.match(/.*_(.+)\.[^.]+$/);
  const dispatcherName = match ? match[1] : "N/A";

  // sends transcription data to transcript component (only for manual file selection)
  useEffect(() => {
    // Skip if transcription was already loaded from API or if no file selected
    if (transcriptionLoaded || !fileName || fileName === "N/A") return;

    // Also skip if fileName is a JSON file (should only process audio files)
    if (fileName.endsWith(".json")) return;

    // reset current time
    setCurrentTime(0);

    // converting audio file name to json
    const baseName = fileName.replace(/\.[^/.]+$/, "");
    const transcriptUrl = `/transcripts/${baseName}.json`;

    fetch(transcriptUrl)
      .then((response) => {
        if (!response.ok) {
          // Don't throw - just log and return
          console.warn(
            `Transcript not found for ${fileName} at ${transcriptUrl}`
          );
          return null;
        }
        return response.json();
      })
      .then((data) => {
        if (data) {
          setTranscription(data);
        }
      })
      .catch((error) => {
        // Catch any errors and log them instead of crashing
        console.error("Error fetching transcript:", error);
      });
  }, [fileName, transcriptionLoaded]); // Added transcriptionLoaded to dependencies

  return (
    <>
      <div className={styles.presentation_header}>
        <p>
          <strong>Dispatcher: </strong>
          {dispatcherName}
        </p>
        <p>
          <strong>Audio File: </strong>
          {fileName}
        </p>
      </div>
      <TranscriptPlayer
        transcriptData={transcription}
        currentTime={currentTime}
      />
      <AudioPlayer path={fileURL || undefined} onProgress={setCurrentTime} />
    </>
  );
}
