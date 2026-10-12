import React from "react";

export default function Header() {
  return (
    <header className="bg-white shadow py-4 px-6 flex items-center justify-between">
      <h1 className="text-xl font-bold text-indigo-600">MarketPulse</h1>
      <span className="text-sm text-gray-500 italic">
        Educational project – Not financial advice
      </span>
    </header>
  );
}
