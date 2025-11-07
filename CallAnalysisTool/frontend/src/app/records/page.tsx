"use client";

import { useEffect } from "react";
import DispatcherList from "@/components/dispatcherList";
import { seedDispatchers } from "@/utils/seedDispatchers";

export default function Records() {
  // useEffect(() => {
  //   seedDispatchers();
  // }, []);

  return (
    <div>
      <DispatcherList />
    </div>
  );
}
