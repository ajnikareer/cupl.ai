with open("frontend/src/components/ui.tsx", "r", encoding="utf-8") as f:
    content = f.read()

target = '''export const Logo = ({ small = false, className = "" }: { small?: boolean; className?: string }) => (
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
);'''

replacement = '''export const Logo = ({ small = false, className = "" }: { small?: boolean; className?: string }) => (
  <div className={clsx("flex items-center", className)}>
    <img
      src="/img/cupl_logo.png"
      alt="cupl.ai — Your AI concierge for life together"
      className={clsx(
        "rounded-xl object-contain shadow-2xs transition",
        small ? "h-10 md:h-11 w-auto max-w-[190px]" : "w-full max-w-[240px] h-auto max-h-[88px]"
      )}
    />
  </div>
);'''

norm_content = content.replace("\r\n", "\n")
norm_target = target.replace("\r\n", "\n")
norm_replacement = replacement.replace("\r\n", "\n")

if norm_target in norm_content:
    updated = norm_content.replace(norm_target, norm_replacement)
    if "\r\n" in content:
        updated = updated.replace("\n", "\r\n")
    with open("frontend/src/components/ui.tsx", "w", encoding="utf-8", newline="") as f:
        f.write(updated)
    print("Successfully enlarged logo in ui.tsx")
else:
    print("Target not found in ui.tsx")

