import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Empty, PageTitle, Spinner } from "../components/ui";

export default function Notifications() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["notifications"], queryFn: () => api("/api/notifications") });
  useEffect(() => { api("/api/notifications/read", { method: "POST" }).then(() => qc.invalidateQueries({ queryKey: ["me"] })).catch(() => {}); }, []);
  if (isLoading) return <Spinner />;
  return (
    <div>
      <PageTitle title="Notifications" />
      {!data?.notifications?.length ? <Empty icon="🔔" title="All caught up" /> : (
        <div className="space-y-2">{data.notifications.map((n: any) => {
          const body = <div className={`card p-4 text-sm ${n.read ? "" : "border-brand/40"}`}>{n.text}<div className="mt-1 text-xs text-mut">{new Date(n.created_at).toLocaleString("en-IN")}</div></div>;
          return n.link ? <Link key={n.id} to={n.link} className="block">{body}</Link> : <div key={n.id}>{body}</div>;
        })}</div>
      )}
    </div>
  );
}
