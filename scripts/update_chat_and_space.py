# Update ChatPage.tsx to remove mock Bali threads and hardcoded banner
with open('frontend/src/pages/ChatPage.tsx', 'r', encoding='utf-8') as f:
    chat_code = f.read()

# Replace DEFAULT_THREADS
target_threads = '''const DEFAULT_THREADS: ChatThread[] = [
  {
    id: "thread_bali",
    title: "Bali honeymoon planning",
    timestamp: Date.now() - 1000 * 60 * 20, // Today, 20 mins ago
    messages: [
      {
        id: "m_bali_1",
        role: "agent",
        text: "Hi Narayan! Welcome back. We're putting together your Bali honeymoon for Nov 15–22. Would you like to check Ubud bamboo villa stays or Seminyak sunset spots first?",
      },
      {
        id: "m_bali_2",
        role: "user",
        text: "Show me some sunset dinner and acoustic spots in Seminyak.",
        voice: true,
      },
      {
        id: "m_bali_3",
        role: "agent",
        text: "Seminyak is renowned for beachfront acoustic lounges! Anjuna Beach Lounge & Jimbaran Bay candlelit tables match both Amruta's romantic aesthetic and your love for live acoustic sets.",
      },
    ],
  },
  {
    id: "thread_sangeet",
    title: "Sangeet playlist ideas",
    timestamp: Date.now() - 1000 * 60 * 60 * 24, // Yesterday
    messages: [
      {
        id: "m_sangeet_1",
        role: "user",
        text: "We need a playlist curve for our Sangeet night.",
      },
      {
        id: "m_sangeet_2",
        role: "agent",
        text: "I've drafted a curve transitioning from nostalgic 90s Bollywood melodies during dinner to high-energy dance anthems for the couple performance!",
      },
      {
        id: "m_sangeet_3",
        role: "user",
        text: "Add some acoustic retro songs for our couple entry.",
      },
      {
        id: "m_sangeet_4",
        role: "agent",
        text: "Perfect! Added acoustic renditions of 'Tum Se Hi' and 'Raabta' for an intimate, cinematic entry.",
      },
    ],
  },
  {
    id: "thread_friday",
    title: "Friday movie & dinner date",
    timestamp: Date.now() - 1000 * 60 * 60 * 48, // 2 days ago
    messages: [
      {
        id: "m_friday_1",
        role: "user",
        text: "Suggest a movie and dinner plan for this Friday.",
      },
      {
        id: "m_friday_2",
        role: "agent",
        text: "How about re-watching 'Yeh Jawaani Hai Deewani' paired with Italian wood-fired pizza and gelato from Olive Bistro? 95% taste match for both of you!",
      },
    ],
  },
  {
    id: "thread_decor",
    title: "Living room decor palette",
    timestamp: Date.now() - 1000 * 60 * 60 * 24 * 5, // 5 days ago
    messages: [
      {
        id: "m_decor_1",
        role: "user",
        text: "Help us balance warm wood with modern minimal home decor.",
      },
      {
        id: "m_decor_2",
        role: "agent",
        text: "A warm teak credenza paired with neutral cream linen upholstery and subtle brass accents brings warmth without cluttering Amruta's minimalist vision.",
      },
    ],
  },
];'''

replacement_threads = '''const DEFAULT_THREADS: ChatThread[] = [];'''

if target_threads in chat_code:
    chat_code = chat_code.replace(target_threads, replacement_threads)
    print("Replaced DEFAULT_THREADS successfully!")
else:
    print("DEFAULT_THREADS target not found!")

# Remove Bali from QUICK_PROMPTS
chat_code = chat_code.replace('"Check flight dates for Bali ✈️"', '"Plan our celebration ✨"')

# Replace activeThreadId initial state
chat_code = chat_code.replace('useState<string>("thread_bali")', 'useState<string>("current")')
chat_code = chat_code.replace('useState(true); // showContinuity', 'useState(false); // showContinuity')
chat_code = chat_code.replace('const [showContinuity, setShowContinuity] = useState(true);', 'const [showContinuity, setShowContinuity] = useState(false);')

# Replace initial greeting if empty
target_greeting = '''          {/* Initial Greeting if chat is empty */}
          {messages.length === 0 && (
            <div className="rise flex gap-2">
              <Avatar size={30} />
              <div className="rounded-2xl rounded-tl-sm border border-line bg-white p-3.5 text-sm shadow-sm text-ink leading-relaxed">
                <div className="h-serif text-base text-brand">Hi {first}! 👋</div>
                What would you like to plan today? Type below or tap <b>Ask cupl AI</b> on the right to speak directly.
              </div>
            </div>
          )}'''

replacement_greeting = '''          {/* Initial Greeting if chat is empty */}
          {messages.length === 0 && (
            <div className="rise flex gap-3">
              <Avatar size={34} />
              <div className="rounded-2xl rounded-tl-sm border border-line bg-white p-4 text-sm shadow-sm text-ink leading-relaxed max-w-lg">
                <div className="h-serif text-base text-brand font-bold mb-1">Hello {first}! Welcome to cupl AI 💕</div>
                <p className="text-mut text-xs leading-relaxed mb-2.5">
                  I am your AI concierge for life together, powered by Qloo Cultural Taste Intelligence. I can assist you with milestone <b>Events</b>, everyday <b>Plans</b>, and weekly <b>Recommendations</b>.
                </p>
                <p className="text-ink text-xs font-medium">
                  Would you like a quick tour of how I can assist you, or is there an upcoming celebration on your mind?
                </p>
              </div>
            </div>
          )}'''

if target_greeting in chat_code:
    chat_code = chat_code.replace(target_greeting, replacement_greeting)
    print("Updated empty greeting successfully!")

# Purge localStorage cache logic
target_local = '''  const [threads, setThreads] = useState<ChatThread[]>(() => {
    try {
      const saved = localStorage.getItem("ww_chat_history");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return DEFAULT_THREADS;
  });'''

replacement_local = '''  const [threads, setThreads] = useState<ChatThread[]>(() => []);'''
if target_local in chat_code:
    chat_code = chat_code.replace(target_local, replacement_local)
    print("Updated threads initial state to empty!")

# Update groups to show active session when empty
target_groups = '''  const groups: { label: string; items: ChatThread[] }[] = [
    { label: "Today", items: todayThreads },
    { label: "Yesterday", items: yesterdayThreads },
    { label: "Previous 7 days", items: olderThreads },
  ].filter((g) => g.items.length > 0);'''

replacement_groups = '''  const groups: { label: string; items: ChatThread[] }[] = threads.length > 0
    ? [
        { label: "Today", items: todayThreads },
        { label: "Yesterday", items: yesterdayThreads },
        { label: "Previous 7 days", items: olderThreads },
      ].filter((g) => g.items.length > 0)
    : [
        {
          label: "Active Session",
          items: [
            {
              id: "current",
              title: "Milestone & Date Concierge",
              timestamp: Date.now(),
              messages,
            },
          ],
        },
      ];'''

if target_groups in chat_code:
    chat_code = chat_code.replace(target_groups, replacement_groups)
    print("Updated groups successfully!")

with open('frontend/src/pages/ChatPage.tsx', 'w', encoding='utf-8') as f:
    f.write(chat_code)
print("ChatPage.tsx saved!")

# Now update SpaceView.tsx for the Gatekeeper card when !plan
with open('frontend/src/pages/SpaceView.tsx', 'r', encoding='utf-8') as f:
    space_code = f.read()

target_empty_plan = '''  if (!plan)
    return (
      <div className="card overflow-hidden text-center">
        <img src={IMG[s.type]} alt="" className="h-40 w-full object-cover" />
        <div className="space-y-3 p-8">
          <div className="h-serif text-2xl text-brand">Ready to weave your plan ✨</div>
          <p className="mx-auto max-w-md text-sm text-mut">Tip: share a few tastes first (chat with cupl or the Me page) and get your partner in — the plan gets far more personal.</p>
          {s.build_error && <ErrorBox error="The last attempt hit a snag. Please try again." />}
          <ErrorBox error={err} />
          <button type="button" onClick={() => build()} className="btn-primary px-6"><Sparkles className="h-4 w-4" /> Build our plan</button>
        </div>
      </div>
    );'''

replacement_empty_plan = '''  if (!plan)
    return (
      <div className="card overflow-hidden text-center max-w-2xl mx-auto shadow-soft border border-border">
        <div className="relative h-44 w-full overflow-hidden">
          <img src={IMG[s.type] || "/img/wedding.jpg"} alt="" className="h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
          <div className="absolute top-4 left-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand text-white text-xs font-semibold shadow-sm">
            <span>🔒</span> Couple Gatekeeper Active
          </div>
          <div className="absolute bottom-4 left-4 right-4 text-left text-white">
            <h1 className="h-serif text-2xl font-bold">{s.title}</h1>
            <p className="text-xs text-white/90">{s.city} • {s.guests || 400} guests • ₹{((s.budget || 2500000) / 100000).toFixed(0)}L budget</p>
          </div>
        </div>
        <div className="space-y-4 p-8">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blush text-brand text-xs font-semibold">
            <span>🌸</span> Awaiting Bride's Tastes & Aesthetic
          </div>
          <h2 className="h-serif text-2xl text-brand font-bold">Groom's Tastes Locked In ✨</h2>
          <p className="mx-auto max-w-lg text-sm text-mut leading-relaxed">
            {user?.displayName ? `${user.displayName.split(" ")[0]}, your` : "Your"} cultural roots, favorite music, and venue scale are saved! To weave an authentic dual-heritage masterplan, your bride needs to be onboarded so her aesthetic, favorite music, and bridal traditions are harmonized with yours.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link to="/app/chat" className="btn-primary w-full sm:w-auto px-6 py-2.5 flex items-center justify-center gap-2 shadow-sm">
              <span>💌</span> Invite Bride in Chat
            </Link>
            <button type="button" onClick={() => build()} className="btn-ghost text-xs text-mut hover:text-brand underline">
              Weave solo preview anyway
            </button>
          </div>
        </div>
      </div>
    );'''

if target_empty_plan in space_code:
    space_code = space_code.replace(target_empty_plan, replacement_empty_plan)
    print("Updated SpaceView.tsx gatekeeper card successfully!")
    with open('frontend/src/pages/SpaceView.tsx', 'w', encoding='utf-8') as f:
        f.write(space_code)
else:
    print("target_empty_plan not found in SpaceView.tsx!")
