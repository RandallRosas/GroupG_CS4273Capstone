"use client";
import { AudioPlayer } from "../AudioPlayer/AudioPlayer";
import { forwardRef, useEffect, useImperativeHandle, useState, useCallback } from "react";
import { TranscriptPlayer } from "../TranscriptPlayer/TranscriptPlayer";
import {
  buildBackendFileUrl,
  fetchBackendFile,
  putBackendFile,
} from "@/lib/api";

interface TranscriptSegment {
  speaker?: string;
  text?: string;
  start: number;
  end: number;
}

interface TranscriptData {
  segments?: TranscriptSegment[];
}

interface PlayerControllerProps {
  transcriptFile?: string;
  audioFile?: string;
  editable?: boolean;
  dispatcherName?: string;
}

export interface PlayerControllerHandle {
  saveTranscriptChanges: () => Promise<boolean>;
  getTranscriptData: () => TranscriptData | null;
}

const PlayerController = forwardRef<PlayerControllerHandle, PlayerControllerProps>(function PlayerController({
  transcriptFile,
  audioFile,
  editable = false,
  dispatcherName,
}: PlayerControllerProps, ref) {
  // states
  const [fileName, setFileName] = useState("N/A");
  const [fileURL, setFileURL] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<TranscriptData | null>(
    null
  );
  const [editableTranscription, setEditableTranscription] = useState<TranscriptData | null>(
    null
  );
  const [currentTime, setCurrentTime] = useState(0);
  const [transcriptionLoaded, setTranscriptionLoaded] = useState(false);

  // Load exact backend record files when provided
  useEffect(() => {
    if (!transcriptFile) {
      return;
    }

    setTranscriptionLoaded(false);
    setTranscription(null);
    setCurrentTime(0);

    fetchBackendFile<TranscriptData>(transcriptFile)
      .then((data) => {
        setTranscription(data);
        setEditableTranscription(data);
        setTranscriptionLoaded(true);
        setFileName(audioFile || transcriptFile);
        setFileURL(audioFile ? buildBackendFileUrl(audioFile) : null);
      })
      .catch((error) => {
        console.error("Error loading transcription:", error);
        setEditableTranscription(null);
        setTranscriptionLoaded(false);
      });
  }, [audioFile, transcriptFile]);

  const resolvedDispatcherName =
    dispatcherName ||
    transcriptFile?.split("_")[0] ||
    audioFile?.split("_")[0] ||
    fileName.split("_")[0];

  useEffect(() => {
    if (transcriptionLoaded || !fileName || fileName === "N/A") return;
    if (fileName.endsWith(".json")) return;
    setCurrentTime(0);
  }, [fileName, transcriptionLoaded]);

  const handleEditSegment = (index: number, speaker: string, text: string) => {
    setEditableTranscription((current) => {
      if (!current?.segments) {
        return current;
      }

      return {
        ...current,
        segments: current.segments.map((segment, segmentIndex) =>
          segmentIndex === index ? { ...segment, speaker, text } : segment
        ),
      };
    });
  };

  const saveTranscriptChanges = useCallback(async () => {
    if (!editable || !transcriptFile || !editableTranscription) {
      return false;
    }

    try {
      await putBackendFile(transcriptFile, editableTranscription);
      const refreshed = await fetchBackendFile<TranscriptData>(transcriptFile);
      setTranscription(refreshed);
      setEditableTranscription(refreshed);
      setCurrentTime(0);
      return true;
    } catch (error) {
      console.error("Error saving transcription:", error);
      return false;
    }
  }, [editable, editableTranscription, transcriptFile]);

  useImperativeHandle(ref, () => ({
    saveTranscriptChanges,
    getTranscriptData: () => editableTranscription || transcription,
  }), [editableTranscription, saveTranscriptChanges, transcription]);

  return (
    <>
      <TranscriptPlayer
        transcriptData={
          editable ? editableTranscription || transcription || undefined : transcription || undefined
        }
        currentTime={currentTime}
        onEditSegment={editable ? handleEditSegment : undefined}
        dispatcherName={resolvedDispatcherName}
      />
      <AudioPlayer path={fileURL || undefined} onProgress={setCurrentTime} />
    </>
  );
});

export default PlayerController;
