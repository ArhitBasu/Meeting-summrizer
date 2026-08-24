import { useState, useEffect, useCallback } from "react";
import type { MeetingResponse } from "../types/meeting";
import { api } from "../services/api";

export function useMeetings() {
  const [meetings, setMeetings] = useState<MeetingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMeetings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getMeetings();
      setMeetings(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to fetch meetings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMeetings();
  }, [fetchMeetings]);

  return { meetings, loading, error, refetch: fetchMeetings };
}
