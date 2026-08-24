import axios from "axios";
import type { MeetingResponse, MeetingDetailResponse, Transcript, Summary } from "../types/meeting";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export const api = {
  uploadMeeting: async (file: File): Promise<MeetingResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await apiClient.post<MeetingResponse>("/meetings/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  getMeetings: async (skip = 0, limit = 100): Promise<MeetingResponse[]> => {
    const response = await apiClient.get<MeetingResponse[]>("/meetings", {
      params: { skip, limit },
    });
    return response.data;
  },

  getMeeting: async (id: number): Promise<MeetingDetailResponse> => {
    const response = await apiClient.get<MeetingDetailResponse>(`/meetings/${id}`);
    return response.data;
  },

  getTranscript: async (id: number): Promise<Transcript> => {
    const response = await apiClient.get<Transcript>(`/meetings/${id}/transcript`);
    return response.data;
  },

  getSummary: async (id: number): Promise<Summary> => {
    const response = await apiClient.get<Summary>(`/meetings/${id}/summary`);
    return response.data;
  },

  deleteMeeting: async (id: number): Promise<void> => {
    await apiClient.delete(`/meetings/${id}`);
  },
};
