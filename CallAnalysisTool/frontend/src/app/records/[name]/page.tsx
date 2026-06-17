"use client";

import React, { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";

import DispatcherDetailsPage from "@/components/DispatcherDetailsPage";

function DispatcherDetailContent() {
  const params = useParams();
  const searchParams = useSearchParams();

  const dispatcherName = params.name as string;
  const startDate = searchParams.get("startDate") || undefined;
  const endDate = searchParams.get("endDate") || undefined;

  return (
    <DispatcherDetailsPage
      dispatcherName={dispatcherName}
      startDate={startDate}
      endDate={endDate}
    />
  );
}

export default function DispatcherDetailPage() {
  return (
    <Suspense fallback={<div className="container mx-auto p-6"><p>Loading...</p></div>}>
      <DispatcherDetailContent />
    </Suspense>
  );
}
