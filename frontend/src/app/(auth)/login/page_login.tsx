"use client";

import { useRouter } from "next/navigation";
import React from "react";

export default function LoginPage() {
  const router = useRouter();
  
  // Always redirect to home page which handles login
  React.useEffect(() => {
    router.replace("/");
  }, [router]);

  return null; // Redirecting...
}