import { useEffect, useState } from "react";

const API = "http://127.0.0.1:8000";
const REFRESH_INTERVAL_MS = 30_000; // 30 seconds

export function useDispatchHistory() {
  const [data, setData] = useState([]);
  const [source, setSource] = useState("local");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/dispatch/", {
          method: "POST"
        });
        const json = await res.json();
        setData(json.data || []);
        setSource(json.source || "local");
      } catch (err) {
        console.warn(err);
      }
    };

    fetchData(); // fetch once immediately

    const interval = setInterval(fetchData, 30_000); // poll every 30s
    return () => clearInterval(interval);
  }, []);

  return { data, source };
}

