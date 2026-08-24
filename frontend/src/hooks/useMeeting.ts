import { useState, useEffect, useCallback } from "react";
import type { MeetingDetailResponse, MeetingStatus } from "../types/meeting";
import { api } from "../services/api";

export function useMeeting(id: number | null) {
  const [meeting, setMeeting] = useState<MeetingDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMeeting = useCallback(async () => {
    if (!id) return;
    try {
      const data = await api.getMeeting(id);
      setMeeting(data);
      setError(null);
      return data;
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to fetch meeting details");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout>;
    let isSubscribed = true;

    const poll = async () => {
      if (!id || !isSubscribed) return;
      
      try {
        const currentMeeting = await fetchMeeting();
        
        const activeStatuses: MeetingStatus[] = [
          "UPLOADED", 
          "TRANSCRIBING", 
          "TRANSCRIBED", 
          "SUMMARIZING"
        ];
        
        if (currentMeeting && activeStatuses.includes(currentMeeting.status)) {
          timeoutId = setTimeout(poll, 3000);
        }
      } catch (e) {
        // Stop polling on error
      }
    };

    if (id) {
      setLoading(true);
      poll();
    }

    return () => {
      isSubscribed = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [id, fetchMeeting]);

  return { meeting, loading, error, refetch: fetchMeeting };
}
