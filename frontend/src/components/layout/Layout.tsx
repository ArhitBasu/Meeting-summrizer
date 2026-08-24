import { Outlet, Link } from "react-router-dom";
import { FileAudio } from "lucide-react";

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 transition-colors">
            <FileAudio className="w-6 h-6" />
            <span className="font-semibold text-lg tracking-tight text-gray-900">Meeting Summarizer</span>
          </Link>
        </div>
      </header>
      <main className="flex-1 w-full max-w-5xl mx-auto p-4 md:p-6 lg:p-8">
        <Outlet />
      </main>
      <footer className="py-6 text-center text-sm text-gray-500 border-t bg-white mt-auto">
        AI Meeting Summarizer - Company Demo
      </footer>
    </div>
  );
}
