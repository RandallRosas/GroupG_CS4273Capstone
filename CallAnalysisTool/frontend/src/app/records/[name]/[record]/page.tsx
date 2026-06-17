"use client";

import React, { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";

import DispatcherDetailsPage from "@/components/DispatcherDetailsPage";

function DispatcherRecordDetailContent() {
  const params = useParams();
  const searchParams = useSearchParams();

  const dispatcherName = params.name as string;
  const recordName = params.record as string;
  const startDate = searchParams.get("startDate") || undefined;
  const endDate = searchParams.get("endDate") || undefined;

  return (
    <DispatcherDetailsPage
      dispatcherName={dispatcherName}
      recordName={recordName}
      startDate={startDate}
      endDate={endDate}
    />
  );
}

export default function DispatcherRecordDetailPage() {
  return (
    <Suspense fallback={<div className="container mx-auto p-6"><p>Loading...</p></div>}>
      <DispatcherRecordDetailContent />
    </Suspense>
  );
}
