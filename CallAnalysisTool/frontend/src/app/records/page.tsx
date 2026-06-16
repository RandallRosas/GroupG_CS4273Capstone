import { Suspense } from "react";
import DispatcherList from "@/components/dispatcherList";

export default function Records() {
  return (
    <Suspense fallback={<div className="p-4 text-center">Loading records...</div>}>
      <DispatcherList />
    </Suspense>
  );
}
