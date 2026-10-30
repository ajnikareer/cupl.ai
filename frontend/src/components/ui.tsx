import clsx from "clsx";

export const Spinner = ({ className = "" }: { className?: string }) => (
  <div className={clsx("h-6 w-6 animate-spin rounded-full border-2 border-blush border-t-brand", className)} />
);

export const CuplMark = ({ className = "h-9 w-9" }: { className?: string }) => (
  <img
    src="/img/avatar.png"
    alt="cupl.ai"
    className={clsx("rounded-xl object-contain shrink-0", className)}
  />
);

export const HeartMark = CuplMark;

export const Logo = ({ small = false, className = "" }: { small?: boolean; className?: string }) => (
  <div className={clsx("flex items-center", className)}>
    <img
      src="/img/cupl_logo.png"
      alt="cupl.ai — Your AI concierge for life together"
      className={clsx(
        "w-auto rounded-xl object-contain shadow-2xs transition",
        small ? "h-9 max-w-[170px]" : "h-11 md:h-12 max-w-[230px]"
      )}
    />
  </div>
);

export const Avatar = ({ size = 40, ring = false, className = "" }: { size?: number; ring?: boolean; className?: string }) => (
  <div className={clsx("relative shrink-0", className)} style={{ width: size, height: size }}>
    {ring && <span className="ring-pulse absolute inset-0 rounded-full border-2 border-brand" />}
    <img src="/img/avatar.png" alt="cupl AI" className="h-full w-full rounded-full object-cover shadow-sm" />
  </div>
);

export const PageTitle = ({ title, sub, right }: { title: string; sub?: string; right?: any }) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 className="h-serif text-3xl text-brand md:text-4xl">{title}</h1>
      {sub && <p className="mt-1 text-sm text-mut">{sub}</p>}
    </div>
    {right}
  </div>
);

export const Empty = ({ icon, title, text, action, image }: { icon?: any; title: string; text?: string; action?: any; image?: string }) => (
  <div className="card overflow-hidden text-center">
    {image && <img src={image} alt="" className="h-40 w-full object-cover" />}
    <div className="flex flex-col items-center gap-2 p-8">
      {!image && <div className="text-3xl">{icon || "💞"}</div>}
      <div className="h-serif text-xl text-brand">{title}</div>
      {text && <p className="max-w-md text-sm text-mut">{text}</p>}
      {action}
    </div>
  </div>
);

export const ErrorBox = ({ error }: { error: any }) =>
  error ? <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{String(error?.message || error)}</div> : null;

export const SPACE_EMOJI: Record<string, string> = { prewedding: "📸", engagement: "💍", wedding: "🕌", honeymoon: "🌴", trip: "✈️", life_beyond: "🎂" };
export const STATE_LABEL: Record<string, string> = {
  draft: "Needs details", ready: "Ready to plan", building: "Weaving plan…", planned: "Planned", stale: "Needs refresh", completed: "Completed",
};
