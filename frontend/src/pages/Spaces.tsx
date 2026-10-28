import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { api } from "../lib/api";
import { Empty, PageTitle, Spinner } from "../components/ui";
import { SpaceCard } from "./Home";

export default function Spaces() {
  const { data, isLoading } = useQuery({ queryKey: ["spaces"], queryFn: () => api("/api/spaces") });
  return (
    <div>
      <PageTitle title="Event Spaces" sub="Each event has its own plan, budget, to-dos and memories." right={<Link to="/app/spaces/new" className="btn-primary"><Plus className="h-4 w-4" /> Create</Link>} />
      {isLoading ? <Spinner /> : data?.spaces?.length ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.spaces.map((s: any) => <SpaceCard key={s.id} s={s} active={s.id === data.active_space_id} />)}
        </div>
      ) : <Empty image="/img/engagement.jpg" title="No event spaces yet" text="Create your first one to start planning." action={<Link to="/app/spaces/new" className="btn-primary mt-2">Create</Link>} />}
    </div>
  );
}
