import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMeeting } from "../hooks/useMeeting";
import { Card, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { ArrowLeft, CheckCircle2, CheckCircle, FileText, LayoutList, CheckSquare, Loader2, AlertCircle } from "lucide-react";
import NotFound from "./NotFound";

export default function MeetingDetails() {
  const { id } = useParams<{ id: string }>();
  const meetingId = id ? parseInt(id, 10) : null;
  const { meeting, loading, error } = useMeeting(meetingId);
  const [activeTab, setActiveTab] = useState<"summary" | "transcript">("summary");

  if (loading && !meeting) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error && !meeting) {
    if (error.includes("404")) return <NotFound />;
    return (
      <div className="p-4 bg-red-50 text-red-600 rounded-md border border-red-200">
        <h2 className="font-semibold mb-2">Error loading meeting</h2>
        <p>{error}</p>
        <Link to="/" className="mt-4 inline-block text-indigo-600 underline">Back to Dashboard</Link>
      </div>
    );
  }

  if (!meeting) return <NotFound />;

  const getPipelineSteps = () => {
    const steps = [
      { id: "UPLOADED", label: "Audio uploaded", completed: true, current: meeting.status === "UPLOADED" },
      { id: "TRANSCRIBING", label: "Transcribing", completed: ["TRANSCRIBED", "SUMMARIZING", "COMPLETED", "SUMMARIZATION_FAILED"].includes(meeting.status), current: meeting.status === "TRANSCRIBING", failed: meeting.status === "TRANSCRIPTION_FAILED" },
      { id: "SUMMARIZING", label: "Analyzing meeting", completed: ["COMPLETED"].includes(meeting.status), current: meeting.status === "SUMMARIZING", failed: meeting.status === "SUMMARIZATION_FAILED" },
      { id: "COMPLETED", label: "Completed", completed: meeting.status === "COMPLETED", current: false }
    ];
    return steps;
  };

  const isProcessing = ["UPLOADED", "TRANSCRIBING", "TRANSCRIBED", "SUMMARIZING"].includes(meeting.status);
  const isFailed = ["TRANSCRIPTION_FAILED", "SUMMARIZATION_FAILED"].includes(meeting.status);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/">
          <Button variant="ghost" size="icon" className="rounded-full">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            {meeting.title || "Processing Meeting..."}
          </h1>
          <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
            <span>{meeting.filename}</span>
            <span>•</span>
            <span>{new Date(meeting.created_at).toLocaleString()}</span>
            <span>•</span>
            <Badge variant={isFailed ? "destructive" : isProcessing ? "secondary" : "default"} className={meeting.status === "COMPLETED" ? "bg-green-600" : ""}>
              {meeting.status}
            </Badge>
          </div>
        </div>
      </div>

      {isProcessing && (
        <Card className="border-indigo-100 bg-indigo-50/50">
          <CardContent className="p-6">
            <h3 className="font-medium text-indigo-900 mb-4 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              AI Pipeline is processing this meeting
            </h3>
            <div className="flex flex-col sm:flex-row gap-4 sm:gap-8">
              {getPipelineSteps().map((step, idx) => (
                <div key={step.id} className="flex items-center gap-2">
                  {step.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  ) : step.failed ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : step.current ? (
                    <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                  )}
                  <span className={`text-sm font-medium ${step.completed ? 'text-gray-900' : step.failed ? 'text-red-600' : step.current ? 'text-indigo-700' : 'text-gray-400'}`}>
                    {step.label}
                  </span>
                  {idx < getPipelineSteps().length - 1 && (
                    <div className="hidden sm:block w-8 border-t-2 border-gray-200 ml-4"></div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {meeting.status === "TRANSCRIPTION_FAILED" && (
        <div className="p-6 bg-red-50 text-red-700 rounded-lg border border-red-200 flex flex-col items-center justify-center text-center">
          <AlertCircle className="w-10 h-10 mb-2 text-red-500" />
          <h2 className="text-lg font-semibold">Transcription Failed</h2>
          <p className="mt-2 text-red-600 max-w-md">We couldn't transcribe this meeting. The audio file might be corrupted or in an unsupported format.</p>
        </div>
      )}

      {meeting.status === "SUMMARIZATION_FAILED" && (
        <div className="p-4 mb-6 bg-orange-50 text-orange-800 rounded-lg border border-orange-200 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 mt-0.5 text-orange-500 flex-shrink-0" />
          <div>
            <h3 className="font-semibold">AI Analysis Failed</h3>
            <p className="text-sm mt-1 text-orange-700">The transcript was generated successfully, but the AI summary could not be produced. You can still read the raw transcript below.</p>
          </div>
        </div>
      )}

      {(meeting.status === "COMPLETED" || meeting.status === "SUMMARIZATION_FAILED") && (
        <div className="flex border-b">
          <button 
            className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'summary' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
            onClick={() => setActiveTab("summary")}
          >
            <LayoutList className="w-4 h-4" />
            Meeting Summary
          </button>
          <button 
            className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'transcript' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
            onClick={() => setActiveTab("transcript")}
          >
            <FileText className="w-4 h-4" />
            Transcript
          </button>
        </div>
      )}

      {activeTab === "summary" && meeting.status === "COMPLETED" && meeting.summary && (
        <div className="space-y-8 animate-in fade-in duration-500 mt-6">
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs">Overview</h2>
            <div className="text-gray-700 leading-relaxed bg-white p-6 rounded-xl border shadow-sm">
              {meeting.summary.overview}
            </div>
          </section>

          <div className="grid md:grid-cols-2 gap-8">
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-500" />
                Key Discussion Points
              </h2>
              <ul className="space-y-3 bg-white p-6 rounded-xl border shadow-sm h-full">
                {meeting.summary.key_points.map((point, i) => (
                  <li key={i} className="flex items-start gap-3 text-gray-700">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 flex-shrink-0" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Decisions
              </h2>
              {meeting.decisions.length > 0 ? (
                <ul className="space-y-3 bg-white p-6 rounded-xl border shadow-sm h-full">
                  {meeting.decisions.map((decision) => (
                    <li key={decision.id} className="flex items-start gap-3 text-gray-700">
                      <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="font-medium">{decision.text}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="bg-white p-6 rounded-xl border shadow-sm h-full flex items-center justify-center text-gray-400 italic">
                  No explicit decisions were made.
                </div>
              )}
            </section>
          </div>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs flex items-center gap-2">
              <CheckSquare className="w-4 h-4 text-orange-500" />
              Action Items
            </h2>
            {meeting.action_items.length > 0 ? (
              <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
                <table className="w-full text-sm text-left">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-6 py-4 font-medium text-gray-600">Task</th>
                      <th className="px-6 py-4 font-medium text-gray-600 w-48">Assignee</th>
                      <th className="px-6 py-4 font-medium text-gray-600 w-48">Deadline</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {meeting.action_items.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50/50">
                        <td className="px-6 py-4 text-gray-900 font-medium">{item.task}</td>
                        <td className="px-6 py-4">
                          {item.assignee ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-md bg-indigo-50 text-indigo-700 text-xs font-medium">
                              {item.assignee}
                            </span>
                          ) : (
                            <span className="text-gray-400 italic">Unassigned</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {item.deadline ? (
                            <span className="text-gray-700">{item.deadline}</span>
                          ) : (
                            <span className="text-gray-400 italic">No deadline</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white p-8 rounded-xl border shadow-sm flex flex-col items-center justify-center text-gray-500 text-center">
                <CheckSquare className="w-8 h-8 text-gray-300 mb-2" />
                <p>No action items were identified in this meeting.</p>
              </div>
            )}
          </section>

          {meeting.participants.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-gray-900 mb-3 uppercase tracking-wider text-xs">Participants</h2>
              <div className="flex flex-wrap gap-2">
                {meeting.participants.map((p) => (
                  <Badge key={p.id} variant="secondary" className="px-3 py-1 text-sm bg-white border shadow-sm">
                    {p.name}
                  </Badge>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {activeTab === "transcript" && (meeting.status === "COMPLETED" || meeting.status === "SUMMARIZATION_FAILED") && meeting.transcript && (
        <div className="bg-white p-6 md:p-8 rounded-xl border shadow-sm animate-in fade-in duration-500 mt-6">
          <div className="prose prose-indigo max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed">
            {meeting.transcript.text}
          </div>
        </div>
      )}
    </div>
  );
}
