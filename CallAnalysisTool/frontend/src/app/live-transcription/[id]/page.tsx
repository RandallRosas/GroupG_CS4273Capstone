"use client";
import { useParams } from "next/navigation";
import PlayerController from "@/components/PlayerController/PlayerController";

export default function LiveTranscriptionPage() {
  const params = useParams();
  const transcriptionId = params.id as string;

  return (
    <>
      <h1>Live Transcription</h1>
      <PlayerController transcriptionId={transcriptionId} />
    </>
  );
}
