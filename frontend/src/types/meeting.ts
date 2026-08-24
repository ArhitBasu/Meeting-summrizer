export type MeetingStatus = 
  | "UPLOADED" 
  | "TRANSCRIBING" 
  | "TRANSCRIBED" 
  | "SUMMARIZING" 
  | "COMPLETED" 
  | "TRANSCRIPTION_FAILED" 
  | "SUMMARIZATION_FAILED";

export interface ActionItem {
  id: number;
  task: string;
  assignee: string | null;
  deadline: string | null;
}

export interface Decision {
  id: number;
  text: string;
}

export interface Participant {
  id: number;
  name: string;
}

export interface Summary {
  overview: string;
  key_points: string[];
}

export interface Transcript {
  text: string;
}

export interface MeetingResponse {
  id: number;
  title: string | null;
  filename: string;
  status: MeetingStatus;
  duration: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface MeetingDetailResponse extends MeetingResponse {
  transcript: Transcript | null;
  summary: Summary | null;
  decisions: Decision[];
  action_items: ActionItem[];
  participants: Participant[];
}
