import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900 mb-4">404</h1>
      <p className="text-lg text-gray-600 mb-8">The page or meeting you're looking for doesn't exist.</p>
      <Link to="/">
        <Button>Return to Dashboard</Button>
      </Link>
    </div>
  );
}
