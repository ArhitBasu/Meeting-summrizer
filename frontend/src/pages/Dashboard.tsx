import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMeetings } from "../hooks/useMeetings";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { UploadCloud, Clock, CheckCircle, AlertCircle, FileAudio, Loader2 } from "lucide-react";
import { api } from "../services/api";

export default function Dashboard() {
  const { meetings, loading, error, refetch } = useMeetings();
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    try {
      const response = await api.uploadMeeting(file);
      refetch();
      navigate(`/meetings/${response.id}`);
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      if (event.target) event.target.value = "";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <Badge variant="default" className="bg-green-600 hover:bg-green-700">Completed</Badge>;
      case "UPLOADED":
      case "TRANSCRIBING":
      case "TRANSCRIBED":
      case "SUMMARIZING":
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-200">Processing</Badge>;
      case "TRANSCRIPTION_FAILED":
      case "SUMMARIZATION_FAILED":
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const stats = {
    total: meetings.length,
    completed: meetings.filter(m => m.status === "COMPLETED").length,
    processing: meetings.filter(m => ["UPLOADED", "TRANSCRIBING", "TRANSCRIBED", "SUMMARIZING"].includes(m.status)).length,
    failed: meetings.filter(m => ["TRANSCRIPTION_FAILED", "SUMMARIZATION_FAILED"].includes(m.status)).length,
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Manage and analyze your meeting recordings.</p>
        </div>
        
        <div className="flex items-center gap-2">
          {uploadError && <span className="text-sm text-red-500">{uploadError}</span>}
          <div className="relative">
            <input
              type="file"
              accept=".mp3,.wav,.m4a"
              onChange={handleFileUpload}
              disabled={uploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            <Button disabled={uploading}>
              {uploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <UploadCloud className="mr-2 h-4 w-4" />}
              Upload Meeting
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Meetings</CardTitle>
            <FileAudio className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.processing}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.failed}</div>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold tracking-tight">Recent Meetings</h2>
        
        {loading ? (
          <div className="flex justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-600 rounded-md border border-red-200">
            {error}
          </div>
        ) : meetings.length === 0 ? (
          <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed">
            <div className="rounded-full bg-indigo-100 p-4 mb-4">
              <UploadCloud className="h-8 w-8 text-indigo-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No meetings yet</h3>
            <p className="text-sm text-gray-500 max-w-sm mb-6">
              Upload your first meeting recording to generate an AI-powered summary, decisions, and action items.
            </p>
            <div className="relative">
              <input
                type="file"
                accept=".mp3,.wav,.m4a"
                onChange={handleFileUpload}
                disabled={uploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
              />
              <Button disabled={uploading}>
                {uploading ? "Uploading..." : "Upload your first meeting"}
              </Button>
            </div>
            <p className="text-xs text-gray-400 mt-4">Supports MP3, WAV, M4A up to 25MB</p>
          </Card>
        ) : (
          <div className="bg-white rounded-md border">
            <div className="relative w-full overflow-auto">
              <table className="w-full caption-bottom text-sm">
                <thead className="[&_tr]:border-b">
                  <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                    <th className="h-12 px-4 text-left align-middle font-medium text-gray-500">Meeting</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-gray-500">Date</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-gray-500">Status</th>
                    <th className="h-12 px-4 text-right align-middle font-medium text-gray-500">Action</th>
                  </tr>
                </thead>
                <tbody className="[&_tr:last-child]:border-0">
                  {meetings.map((meeting) => (
                    <tr key={meeting.id} className="border-b transition-colors hover:bg-gray-50 data-[state=selected]:bg-muted">
                      <td className="p-4 align-middle">
                        <div className="font-medium">{meeting.title || "Untitled Meeting"}</div>
                        <div className="text-xs text-gray-500">{meeting.filename}</div>
                      </td>
                      <td className="p-4 align-middle text-gray-500">
                        {new Date(meeting.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-4 align-middle">
                        {getStatusBadge(meeting.status)}
                      </td>
                      <td className="p-4 align-middle text-right">
                        <Link to={`/meetings/${meeting.id}`}>
                          <Button variant="outline" size="sm">View Details</Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
