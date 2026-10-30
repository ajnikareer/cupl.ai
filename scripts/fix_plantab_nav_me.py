with open('frontend/src/pages/SpaceView.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

target = '''function PlanTab({ s }: { s: any }) {
  const qc = useQueryClient();'''

replacement = '''function PlanTab({ s }: { s: any }) {
  const qc = useQueryClient();
  const nav = useNavigate();
  const { data: me } = useQuery({ queryKey: ["me"], queryFn: () => api("/api/me") });'''

if target in c:
    c = c.replace(target, replacement)
    with open('frontend/src/pages/SpaceView.tsx', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Added nav and me to PlanTab successfully!")
else:
    print("target not found in SpaceView.tsx")
