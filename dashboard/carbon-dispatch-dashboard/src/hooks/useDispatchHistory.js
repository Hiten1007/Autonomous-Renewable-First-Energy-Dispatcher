import { useEffect, useState } from "react";
import fallbackData from "../mock/dispatch_data.json";

const API = "http://127.0.0.1:8000";

export function useDispatchHistory(windowMin = 30) {
  const [data, setData] = useState(fallbackData);
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState("local");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);

      try {
        const res = await fetch(`${API}/dispatch/`, {
          method: "POST"
        });

        if (!res.ok) throw new Error("Dispatch failed");

        const json = await res.json();

        if (!cancelled && Array.isArray(json) && json.length) {
          setData(prev => mergeByTimestamp(prev, json));
          setSource("backend");
        }
      } catch (err) {
        console.warn("Using local dispatch snapshot");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [windowMin]);

  return { data, loading, source };
}


function mergeByTimestamp(oldData, newData) {
  const map = new Map();

  oldData.forEach(d => {
    map.set(d.timestamp, d);
  });

  newData.forEach(d => {
    map.set(d.timestamp, {
      ...map.get(d.timestamp),
      ...d
    });
  });

  return Array.from(map.values()).sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  );
}
