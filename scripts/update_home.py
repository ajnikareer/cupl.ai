with open('frontend/src/pages/Home.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    'import { AudioLines, Plus } from "lucide-react";',
    'import { AudioLines, Plus, Sparkles } from "lucide-react";'
)
text = text.replace(
    '<Link to="/app/spaces/new" className="btn-primary px-4 py-2 text-sm"><Plus className="h-4 w-4" /> Create Event Space</Link>',
    '<Link to="/app/chat" className="btn-primary px-5 py-2.5 text-sm shadow-xs inline-flex items-center gap-2"><Sparkles className="h-4 w-4" /> Start with cupl AI</Link>'
)
text = text.replace(
    '<h2 className="h-serif text-2xl text-brand">Your Event Spaces</h2>',
    '<h2 className="h-serif text-2xl text-brand">Your Events</h2>'
)
text = text.replace(
    '<Plus /> Create New Event Space',
    '<Plus /> Create New Event'
)
text = text.replace(
    'title="No event spaces yet"',
    'title="No events yet"'
)
text = text.replace(
    'action={<Link to="/app/spaces/new" className="btn-primary mt-2">Create Event Space</Link>}',
    'action={<Link to="/app/chat" className="btn-primary mt-2 inline-flex items-center gap-2"><Sparkles className="h-4 w-4" /> Start with cupl AI</Link>}'
)

with open('frontend/src/pages/Home.tsx', 'w', encoding='utf-8') as f:
    f.write(text)

print('Success updating Home.tsx!')

