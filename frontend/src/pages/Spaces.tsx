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
      <PageTitle title="👑 Our Events" sub="Milestone celebration masterplans: Weddings, Preweddings, Engagements, Honeymoons, and Trips" right={<Link to="/app/spaces/new" className="btn-primary"><Plus className="h-4 w-4" /> New Event</Link>} />
      {isLoading ? <Spinner /> : data?.spaces?.length ? (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.spaces.map((s: any) => <SpaceCard key={s.id} s={s} active={s.id === data.active_space_id} />)}
        </div>
      ) : <Empty image="/img/engagement.jpg" title="No event spaces yet" text="Create your milestone celebration space to unlock multi-generational music curves, anti-waste catering, and ceremony blueprints." action={<Link to="/app/spaces/new" className="btn-primary mt-2">Create</Link>} />}
    </div>
  );
}
