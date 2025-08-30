import React, { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CalendarDays,
  QrCode,
  Trophy,
  Home,
  Plus,
  Bell,
  LogIn,
  ChevronLeft,
  Users,
  MapPin,
  Clock,
  Check,
  Sparkles,
  Settings,
} from "lucide-react";

// shadcn/ui
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

// --- Sample Data ---
const SAMPLE_EVENTS = [
  {
    id: "e1",
    name: "Tech Fest '25",
    date: "Sep 12, 2025",
    venue: "Main Auditorium",
    tags: ["AI", "Robotics"],
    sessions: [
      { id: "s1", time: "10:00", title: "Opening Keynote: Future of AI", hall: "A1" },
      { id: "s2", time: "11:30", title: "Hands-on: Build a Bot", hall: "Lab 2" },
      { id: "s3", time: "14:00", title: "Panel: Startups & You", hall: "A3" },
    ],
  },
  {
    id: "e2",
    name: "Cultural Carnival",
    date: "Oct 04, 2025",
    venue: "Open Grounds",
    tags: ["Music", "Food"],
    sessions: [
      { id: "s4", time: "12:00", title: "Battle of Bands", hall: "Stage 2" },
      { id: "s5", time: "15:30", title: "Street Food Expo", hall: "Food Court" },
    ],
  },
];

const interestsCatalog = ["AI", "Robotics", "Web", "Music", "Food", "Workshops"];

function DeviceShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-[380px] max-w-full rounded-3xl bg-white shadow-xl ring-1 ring-slate-200 overflow-hidden">
        {children}
      </div>
    </div>
  );
}

function TopBar({ title, onBack }: { title: string; onBack?: () => void }) {
  return (
    <div className="sticky top-0 z-10 bg-white/90 backdrop-blur border-b">
      <div className="flex items-center gap-2 p-3">
        {onBack ? (
          <Button variant="ghost" size="icon" onClick={onBack} className="rounded-2xl">
            <ChevronLeft className="h-5 w-5" />
          </Button>
        ) : (
          <Button variant="ghost" size="icon" className="rounded-2xl">
            <Sparkles className="h-5 w-5" />
          </Button>
        )}
        <div className="font-semibold text-lg flex-1 text-center -ml-10">{title}</div>
        <Button variant="ghost" size="icon" className="rounded-2xl">
          <Bell className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}

function BottomNav({ current, setCurrent }: { current: string; setCurrent: (s: string) => void }) {
  const NavBtn = ({ id, icon: Icon, label }: any) => (
    <button
      onClick={() => setCurrent(id)}
      className={`flex flex-col items-center justify-center gap-1 p-2 flex-1 ${
        current === id ? "text-slate-900" : "text-slate-500"
      }`}
    >
      <Icon className={`h-5 w-5 ${current === id ? "" : "opacity-70"}`} />
      <span className="text-[10px] tracking-wide">{label}</span>
    </button>
  );
  return (
    <div className="sticky bottom-0 bg-white/95 backdrop-blur border-t grid grid-cols-4">
      <NavBtn id="home" icon={Home} label="Home" />
      <NavBtn id="schedule" icon={CalendarDays} label="Schedule" />
      <NavBtn id="qr" icon={QrCode} label="Pass" />
      <NavBtn id="rewards" icon={Trophy} label="Rewards" />
    </div>
  );
}

function QRPreview({ name = "Sanath B Rao", event = "Tech Fest '25" }) {
  // Simple inline SVG to mimic QR. Replace with real lib later if needed.
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="rounded-2xl p-4 border w-56 h-56 grid place-items-center">
        <svg viewBox="0 0 120 120" className="w-44 h-44">
          <rect x="0" y="0" width="120" height="120" fill="white" />
          <g fill="black">
            {Array.from({ length: 200 }).map((_, i) => {
              const x = (i * 17) % 120;
              const y = (i * 43) % 120;
              return <rect key={i} x={x} y={y} width="4" height="4" rx="1" />;
            })}
            <rect x="8" y="8" width="24" height="24" />
            <rect x="88" y="8" width="24" height="24" />
            <rect x="8" y="88" width="24" height="24" />
          </g>
        </svg>
      </div>
      <div className="text-center">
        <div className="font-semibold">{name}</div>
        <div className="text-sm text-slate-600">{event}</div>
      </div>
    </div>
  );
}

export default function App() {
  const [screen, setScreen] = useState<
    "login" | "home" | "event" | "schedule" | "qr" | "rewards" | "admin"
  >("login");

  const [email, setEmail] = useState("");
  const [name, setName] = useState("Sanath B Rao");
  const [interests, setInterests] = useState<string[]>(["AI", "Workshops"]);
  const [selectedEvent, setSelectedEvent] = useState<string | null>("e1");
  const [mySessions, setMySessions] = useState<string[]>([]);
  const [points, setPoints] = useState(40);

  const currentEvent = useMemo(
    () => SAMPLE_EVENTS.find((e) => e.id === selectedEvent) || SAMPLE_EVENTS[0],
    [selectedEvent]
  );

  const recommended = useMemo(() => {
    return SAMPLE_EVENTS.filter((e) => e.tags.some((t) => interests.includes(t)));
  }, [interests]);

  const toggleInterest = (tag: string) => {
    setInterests((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const addToSchedule = (sessionId: string) => {
    setMySessions((prev) => (prev.includes(sessionId) ? prev : [...prev, sessionId]));
  };

  const checkIn = (sessionId: string) => {
    if (!mySessions.includes(sessionId)) return; // only if planned
    setPoints((p) => p + 5);
  };

  return (
    <DeviceShell>
      {/* Top */}
      <TopBar
        title={
          screen === "login"
            ? "Smart Event Organizer"
            : screen === "home"
            ? "Discover"
            : screen === "event"
            ? currentEvent.name
            : screen === "schedule"
            ? "My Schedule"
            : screen === "qr"
            ? "My Pass"
            : screen === "rewards"
            ? "Rewards"
            : "Organizer"
        }
        onBack={screen !== "home" && screen !== "login" ? () => setScreen("home") : undefined}
      />

      {/* Body */}
      <div className="p-4 space-y-4">
        <AnimatePresence mode="wait">
          {screen === "login" && (
            <motion.div
              key="login"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-xl">Welcome</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name</Label>
                    <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@college.edu"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Interests</Label>
                    <div className="flex flex-wrap gap-2">
                      {interestsCatalog.map((t) => (
                        <Badge
                          key={t}
                          variant={interests.includes(t) ? "default" : "outline"}
                          onClick={() => toggleInterest(t)}
                          className="cursor-pointer select-none"
                        >
                          {t}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button className="w-full rounded-2xl" onClick={() => setScreen("home")}> 
                    <LogIn className="mr-2 h-4 w-4" /> Continue
                  </Button>
                </CardContent>
              </Card>

              <Button variant="outline" className="w-full rounded-2xl" onClick={() => setScreen("admin")}> 
                <Settings className="mr-2 h-4 w-4" /> Organizer Mode
              </Button>
            </motion.div>
          )}

          {screen === "home" && (
            <motion.div
              key="home"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Recommended for you</CardTitle>
                </CardHeader>
                <CardContent className="flex gap-3 overflow-auto no-scrollbar pb-2">
                  {recommended.map((e) => (
                    <div
                      key={e.id}
                      className="min-w-[220px] rounded-2xl border p-3 hover:shadow transition cursor-pointer"
                      onClick={() => {
                        setSelectedEvent(e.id);
                        setScreen("event");
                      }}
                    >
                      <div className="font-semibold">{e.name}</div>
                      <div className="text-sm text-slate-600 flex items-center gap-1 mt-1">
                        <CalendarDays className="h-4 w-4" /> {e.date}
                      </div>
                      <div className="text-sm text-slate-600 flex items-center gap-1">
                        <MapPin className="h-4 w-4" /> {e.venue}
                      </div>
                      <div className="flex gap-2 mt-2">
                        {e.tags.map((t) => (
                          <Badge key={t} variant="secondary">{t}</Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">All Events</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {SAMPLE_EVENTS.map((e) => (
                    <div key={e.id} className="rounded-2xl border p-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-semibold">{e.name}</div>
                          <div className="text-sm text-slate-600 flex items-center gap-1 mt-1">
                            <CalendarDays className="h-4 w-4" /> {e.date}
                          </div>
                          <div className="text-sm text-slate-600 flex items-center gap-1">
                            <MapPin className="h-4 w-4" /> {e.venue}
                          </div>
                        </div>
                        <Button
                          className="rounded-2xl"
                          onClick={() => {
                            setSelectedEvent(e.id);
                            setScreen("event");
                          }}
                        >
                          View
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {screen === "event" && (
            <motion.div
              key="event"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Sessions</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {currentEvent.sessions.map((s) => (
                    <div key={s.id} className="rounded-2xl border p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm text-slate-600 flex items-center gap-1">
                            <Clock className="h-4 w-4" /> {s.time} • Hall {s.hall}
                          </div>
                          <div className="font-medium">{s.title}</div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" className="rounded-2xl" onClick={() => addToSchedule(s.id)}>
                            Add
                          </Button>
                          <Button className="rounded-2xl" onClick={() => checkIn(s.id)}>
                            Check-in
                          </Button>
                        </div>
                      </div>
                      {mySessions.includes(s.id) && (
                        <div className="mt-2 text-xs text-green-700 flex items-center gap-1">
                          <Check className="h-3 w-3" /> Added to your schedule
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {screen === "schedule" && (
            <motion.div
              key="schedule"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Today</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  {mySessions.length === 0 && (
                    <div className="text-sm text-slate-600">No sessions yet. Add from an event.</div>
                  )}
                  {SAMPLE_EVENTS.flatMap((e) => e.sessions)
                    .filter((s) => mySessions.includes(s.id))
                    .map((s) => (
                      <div key={s.id} className="rounded-2xl border p-3 flex items-center justify-between">
                        <div>
                          <div className="text-sm text-slate-600 flex items-center gap-1">
                            <Clock className="h-4 w-4" /> {s.time}
                          </div>
                          <div className="font-medium">{s.title}</div>
                        </div>
                        <Button className="rounded-2xl" onClick={() => checkIn(s.id)}>Check-in</Button>
                      </div>
                    ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {screen === "qr" && (
            <motion.div
              key="qr"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Entry Pass</CardTitle>
                </CardHeader>
                <CardContent className="grid place-items-center gap-4">
                  <QRPreview name={name} event={currentEvent.name} />
                  <div className="text-xs text-slate-600">Show this QR at the gate</div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {screen === "rewards" && (
            <motion.div
              key="rewards"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Your Rewards</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="rounded-2xl border p-4 flex items-center justify-between">
                    <div>
                      <div className="text-sm text-slate-600">Points</div>
                      <div className="text-2xl font-bold">{points}</div>
                    </div>
                    <Trophy className="h-10 w-10" />
                  </div>
                  <div className="rounded-2xl border p-4">
                    <div className="font-medium mb-2">Leaderboard (demo)</div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span>Priya</span><span>55</span></div>
                      <div className="flex justify-between"><span>Arjun</span><span>50</span></div>
                      <div className="flex justify-between"><span>{name}</span><span>{points}</span></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {screen === "admin" && (
            <motion.div
              key="admin"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-4"
            >
              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Create Event (Prototype)</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3">
                  <div className="grid gap-2">
                    <Label>Event name</Label>
                    <Input placeholder="e.g., Smart Expo 2025" />
                  </div>
                  <div className="grid gap-2">
                    <Label>Date</Label>
                    <Input placeholder="YYYY-MM-DD" />
                  </div>
                  <div className="grid gap-2">
                    <Label>Venue</Label>
                    <Input placeholder="Main Hall" />
                  </div>
                  <div className="grid gap-2">
                    <Label>About</Label>
                    <Textarea placeholder="Short description" />
                  </div>
                  <Button className="rounded-2xl"><Plus className="h-4 w-4 mr-2"/>Add Event</Button>
                </CardContent>
              </Card>

              <Card className="rounded-2xl">
                <CardHeader>
                  <CardTitle className="text-lg">Registrations (Demo)</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>Tech Fest '25</span>
                    <Badge>124</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Cultural Carnival</span>
                    <Badge>88</Badge>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Navigation (hide on login & admin) */}
      {!(screen === "login" || screen === "admin") && (
        <BottomNav current={screen} setCurrent={setScreen as any} />
      )}
    </DeviceShell>
  );
}
