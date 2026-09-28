"use client";
import Preparation from "./Preparation";
import preparationCatalog from "./preparation.json";
import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  LayoutDashboard,
  BookOpen,
  ClipboardList,
  ChartNoAxesCombined,
  Bookmark,
  Settings,
  Sparkles,
  ArrowUpRight,
  ArrowRight,
  ChevronRight,
  ChevronLeft,
  Clock,
  Target,
  Check,
  CheckCircle2,
  X,
  Flag,
  Search,
  Upload,
  Plus,
  ShieldCheck,
  Zap,
  Monitor,
  Brain,
  Calculator,
  Globe2,
  FlaskConical,
  LogOut,
  Sun,
  Moon,
  Signal,
  Play,
  RotateCcw,
  Download,
  LoaderCircle,
  AlertCircle,
  PanelLeft,
} from "lucide-react";
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Checkbox } from "@/components/ui/checkbox";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Toaster, toast } from "sonner";
import { api, configure, setToken, subjects, Question } from "./api";
import seedData from "./seed.json";
const seed = seedData as Question[];
const icons = [FlaskConical, Monitor, Calculator, Brain, Globe2];
const abbreviations = [
  "Science & Engineering",
  "Computers",
  "Mathematics",
  "Reasoning",
  "General Awareness",
];
const distribution = [35, 20, 20, 15, 10];
const initialStats = {
  total: seed.length,
  topics: new Set(seed.map((q) => q.topic)).size,
  sources: { ORIGINAL: seed.length },
  statuses: { ACTIVE: seed.length },
  subjects: Object.fromEntries(
    subjects.map((s) => [s, seed.filter((q) => q.subject === s).length]),
  ),
};
const configsDefault = [
  {
    id: "exam-prep",
    name: "Exam preparation · verified PYQs + hard patterns",
    duration_minutes: 90,
    distribution: Object.fromEntries(
      subjects.map((s, i) => [s, distribution[i]]),
    ),
    source_mix: { PYQ: 50, PYQ_PATTERN: 50 },
    difficulty_mix: { Hard: 100 },
    cooldown_days: 365,
    correct_marks: 1,
    wrong_penalty: 1 / 3,
  },
  {
    id: "grade1",
    name: "Basic concepts · 100 questions",
    duration_minutes: 90,
    distribution: Object.fromEntries(
      subjects.map((s, i) => [s, distribution[i]]),
    ),
    source_mix: { ORIGINAL: 100 },
    difficulty_mix: { Easy: 30, Medium: 50, Hard: 20 },
    cooldown_days: 7,
    correct_marks: 1,
    wrong_penalty: 1 / 3,
  },
  {
    id: "quick",
    name: "Quick Practice · 10 Questions",
    duration_minutes: 10,
    distribution: Object.fromEntries(
      subjects.map((s, i) => [s, [4, 2, 2, 1, 1][i]]),
    ),
    source_mix: { ORIGINAL: 100 },
    difficulty_mix: { Easy: 30, Medium: 50, Hard: 20 },
    cooldown_days: 7,
    correct_marks: 1,
    wrong_penalty: 1 / 3,
  },
];
type Any = Record<string, any>;
function Pick({
  value,
  onChange,
  items,
  label,
}: {
  value: string;
  onChange: (v: string) => void;
  items: string[];
  label: string;
}) {
  return (
    <Select
      value={value || "__all"}
      onValueChange={(v) => onChange(v === "__all" ? "" : v)}
    >
      <SelectTrigger aria-label={label}>
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        {items.map((v) => (
          <SelectItem key={v} value={v || "__all"}>
            {v || label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
function Badge({
  children,
  kind = "neutral",
}: {
  children: React.ReactNode;
  kind?: string;
}) {
  return <span className={"badge " + kind}>{children}</span>;
}
// Renders the optional structured explanation fields (concept/formula/given/
// calculation/final_answer/why_correct/why_wrong) in a fixed teaching order,
// falling back to the plain `explanation` text when none are present. Old
// questions and conceptual questions (no formula/calculation) keep working
// unchanged. Never render a heading for an empty section.
type ExplanationData = {
  explanation?: string;
  concept?: string;
  formula?: string;
  given?: string;
  calculation?: string;
  final_answer?: string;
  why_correct?: string;
  why_wrong?: Record<string, string> | null;
  correct_option?: string;
};
function ExplanationBlock({
  data,
  selected,
}: {
  data: ExplanationData;
  selected?: string | null;
}) {
  const wrongEntries = Object.entries(data.why_wrong || {});
  const hasStructured = Boolean(
    data.concept ||
      data.formula ||
      data.given ||
      data.calculation ||
      data.final_answer ||
      data.why_correct ||
      wrongEntries.length,
  );
  if (!hasStructured) {
    return data.explanation ? <p>{data.explanation}</p> : null;
  }
  const wrongSelected =
    selected && data.correct_option && selected !== data.correct_option
      ? selected
      : null;
  const selectedReason = wrongSelected
    ? data.why_wrong?.[wrongSelected]
    : undefined;
  const otherReasons = wrongEntries.filter(([k]) => k !== wrongSelected);
  return (
    <div className="structured-explanation">
      {data.concept && (
        <div className="explanation-section">
          <h4>Concept</h4>
          <p>{data.concept}</p>
        </div>
      )}
      {data.why_correct && (
        <div className="explanation-section">
          <h4>Why correct</h4>
          <p>{data.why_correct}</p>
        </div>
      )}
      {data.formula && (
        <div className="explanation-section">
          <h4>Formula</h4>
          <pre className="explanation-pre">{data.formula}</pre>
        </div>
      )}
      {data.given && (
        <div className="explanation-section">
          <h4>Given</h4>
          <pre className="explanation-pre">{data.given}</pre>
        </div>
      )}
      {data.calculation && (
        <div className="explanation-section">
          <h4>Calculation</h4>
          <pre className="explanation-pre">{data.calculation}</pre>
        </div>
      )}
      {data.final_answer && (
        <div className="explanation-section">
          <h4>Final answer</h4>
          <p>
            <strong>{data.final_answer}</strong>
          </p>
        </div>
      )}
      {wrongSelected && selectedReason && (
        <div className="explanation-section wrong">
          <h4>Why your answer is wrong</h4>
          <p>
            Your answer: {wrongSelected}. {selectedReason}
          </p>
        </div>
      )}
      {otherReasons.length > 0 && (
        <div className="explanation-section">
          <h4>Why other options are wrong</h4>
          {otherReasons.map(([k, reason]) => (
            <p key={k}>
              <b>{k}.</b> {reason}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
// Admin-editor convenience: why_wrong is stored/sent as {optionLetter: reason},
// but is easiest to edit as plain lines like "A: reason". These two helpers
// keep the editor's `why_wrong` field as the real object at all times, only
// converting to/from text at render time, so saving never needs a separate
// parse step.
function whyWrongToText(value?: Record<string, string> | null) {
  if (!value) return "";
  return Object.entries(value)
    .map(([k, reason]) => `${k}: ${reason}`)
    .join("\n");
}
function textToWhyWrong(text: string): Record<string, string> | null {
  const result: Record<string, string> = {};
  for (const line of text.split("\n")) {
    const m = line.trim().match(/^([A-Da-d])\s*[:.-]\s*(.+)$/);
    if (m) result[m[1].toUpperCase()] = m[2].trim();
  }
  return Object.keys(result).length ? result : null;
}
// A single malformed question (or any other unexpected render error) should
// never take down the whole app — it should be contained to the page the
// person was on, with a way back to the dashboard.
class PageErrorBoundary extends React.Component<
  { children: React.ReactNode; onReset?: () => void },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; onReset?: () => void }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error: unknown) {
    console.error("SignalPrep UI error:", error);
  }
  render() {
    if (this.state.hasError) {
      return (
        <Empty title="Something went wrong showing this page.">
          This won't affect your saved progress.{" "}
          {this.props.onReset && (
            <button
              className="btn secondary"
              onClick={() => {
                this.setState({ hasError: false });
                this.props.onReset?.();
              }}
            >
              Back to dashboard
            </button>
          )}
        </Empty>
      );
    }
    return this.props.children;
  }
}
function Empty({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="empty">
      <Target size={32} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
function Stat({
  icon: Icon,
  label,
  value,
  foot,
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
  foot: string;
}) {
  return (
    <div className="stat">
      <div className="stat-label">
        {label}
        <Icon size={18} />
      </div>
      <strong>{value}</strong>
      <span>{foot}</span>
    </div>
  );
}
export default function SignalPrep() {
  const [page, setPage] = useState("Dashboard"),
    [connected, setConnected] = useState(false),
    [health, setHealth] = useState<Any>({}),
    [me, setMe] = useState<Any | null>(null),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false);
  const [stats, setStats] = useState<Any>(initialStats),
    [analytics, setAnalytics] = useState<Any>({
      history: [],
      topics: {},
      subjects: {},
      weak_topics: [],
      completed: 0,
    }),
    [configs, setConfigs] = useState<Any[]>(configsDefault),
    [attempts, setAttempts] = useState<Any[]>([]);
  const [settings, setSettings] = useState(false),
    [apiUrl, setApiUrl] = useState(""),
    [dark, setDark] = useState(false),
    [login, setLogin] = useState(false),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [signup, setSignup] = useState(false),
    [profileName, setProfileName] = useState("");
  const [startDialog, setStartDialog] = useState(false),
    [mode, setMode] = useState("PRACTICE"),
    [configId, setConfigId] = useState("grade1"),
    [weak, setWeak] = useState(false),
    [attempt, setAttempt] = useState<Any | null>(null),
    [idx, setIdx] = useState(0),
    [feedback, setFeedback] = useState<Any | null>(null),
    // Practice-mode feedback already shown for a question, keyed by question
    // id, so navigating away and back (Next/Previous/palette) re-shows the
    // same explanation instead of hiding it until the question is re-answered.
    [feedbackHistory, setFeedbackHistory] = useState<Record<string, Any>>({}),
    [remaining, setRemaining] = useState(0),
    [confirmSubmit, setConfirmSubmit] = useState(false);
  const [topicsBySubject, setTopicsBySubject] = useState<
    Record<string, string[]>
  >({}),
    [pSubject, setPSubject] = useState(""),
    [pTopic, setPTopic] = useState(""),
    [pDifficulty, setPDifficulty] = useState(""),
    [pSource, setPSource] = useState(""),
    [pCount, setPCount] = useState(10);
  const [search, setSearch] = useState(""),
    [subject, setSubject] = useState(""),
    [difficulty, setDifficulty] = useState(""),
    [source, setSource] = useState(""),
    [status, setStatus] = useState(""),
    [topic, setTopic] = useState(""),
    [year, setYear] = useState(""),
    [bankPage, setBankPage] = useState(1),
    [bank, setBank] = useState<Any>({
      items: seed.slice(0, 25),
      total: 190,
      pages: 8,
    }),
    [preview, setPreview] = useState<Question | null>(null),
    [reveal, setReveal] = useState(false);
  const [editor, setEditor] = useState<Any | null>(null),
    [reviewNotes, setReviewNotes] = useState(""),
    [verifyPyq, setVerifyPyq] = useState(false),
    [importResult, setImportResult] = useState<Any | null>(null),
    [jobs, setJobs] = useState<Any[]>([]);
  const [gen, setGen] = useState<Any>({
      subject: subjects[0],
      topic: "Transformers",
      subtopic: "",
      difficulty: "Medium",
      count: 5,
      source_type: "ORIGINAL",
      concept: "",
      parent_question_id: "",
      style: "Mixed conceptual and numerical",
    }),
    [newConfigId, setNewConfigId] = useState(""),
    [configEdit, setConfigEdit] = useState(""),
    [profileDraft, setProfileDraft] = useState("");
  const timerOffset = useRef(0),
    autoSubmit = useRef(false),
    saving = useRef(false);
  const refresh = useCallback(async () => {
    const [st, an, co, at] = await Promise.all([
      api("/stats"),
      api("/analytics"),
      api("/configs"),
      api("/attempts"),
    ]);
    setStats(st);
    setAnalytics(an);
    setConfigs(co);
    setAttempts(at);
  }, []);
  const connect = useCallback(async () => {
    try {
      const h = await api("/health");
      setHealth(h);
      setConnected(true);
      if (h.development_auth) {
        const u = await api("/me");
        setMe(u);
        setProfileDraft(u.name);
        await refresh();
      } else {
        setMe(null);
      }
    } catch {
      setConnected(false);
      setMe(null);
    } finally {
      setLoading(false);
    }
  }, [refresh]);
  useEffect(() => {
    const url = localStorage.getItem("signalprep-api") || "";
    setApiUrl(url);
    if (url) configure(url);
    const theme = localStorage.getItem("signalprep-theme") === "dark";
    setDark(theme);
    document.documentElement.classList.toggle("dark", theme);
    void connect();
  }, [connect]);
  useEffect(() => {
    setBankPage(1);
  }, [search, subject, difficulty, source, status, topic, year, page]);
  useEffect(() => {
    if (connected && me) api("/topics").then(setTopicsBySubject).catch(() => {});
  }, [connected, me]);
  useEffect(() => {
    setFeedbackHistory({});
  }, [attempt?.id]);
  const loadBank = useCallback(async () => {
    if (!["Question Bank", "Bookmarks", "Admin Review"].includes(page)) return;
    if (!connected || !me) {
      let items = seed.filter(
        (q) =>
          (!subject || q.subject === subject) &&
          (!difficulty || q.difficulty === difficulty) &&
          (!source || q.source_type === source) &&
          (!topic || q.topic.toLowerCase().includes(topic.toLowerCase())) &&
          (!search ||
            q.question_text.toLowerCase().includes(search.toLowerCase())) &&
          (!year || q.exam_year === Number(year)) &&
          (!status || q.status === status),
      );
      if (page === "Bookmarks" || page === "Admin Review") items = [];
      setBank({
        items: items.slice((bankPage - 1) * 25, bankPage * 25),
        total: items.length,
        pages: Math.max(1, Math.ceil(items.length / 25)),
      });
      return;
    }
    try {
      setBank(
        await api(
          "/questions?" +
            new URLSearchParams({
              search,
              subject,
              difficulty,
              source_type: source,
              topic,
              status: page === "Admin Review" ? "PENDING_REVIEW" : status,
              year: year || "",
              page: String(bankPage),
              bookmarked: String(page === "Bookmarks"),
            })
              .toString()
              .replace("year=&", ""),
        ),
      );
    } catch (e) {
      toast.error((e as Error).message);
    }
  }, [
    page,
    connected,
    me,
    subject,
    difficulty,
    source,
    status,
    topic,
    search,
    year,
    bankPage,
  ]);
  useEffect(() => {
    const t = setTimeout(() => void loadBank(), 180);
    return () => clearTimeout(t);
  }, [loadBank]);
  useEffect(() => {
    if (page === "AI Generator" && me?.role === "admin")
      api("/jobs")
        .then(setJobs)
        .catch((e) => toast.error(e.message));
  }, [page, me]);
  async function act(fn: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function needAccount() {
    if (!connected) {
      setSettings(true);
      return false;
    }
    if (!me) {
      setLogin(true);
      return false;
    }
    return true;
  }
  function navigate(p: string) {
    setPage(p);
    setSearch("");
    setSubject("");
    setTopic("");
    setStatus("");
    setDifficulty("");
    setSource("");
    setYear("");
  }
  function openStart(m = "EXAM", id = "grade1", isWeak = false) {
    setMode(m);
    setConfigId(m === "EXAM" && id === "grade1" ? "exam-prep" : id);
    setWeak(isWeak);
    setStartDialog(true);
  }
  async function startTest() {
    await act(async () => {
      if (!needAccount()) return;
      const a = await api("/attempts", "POST", {
        config_id: configId,
        mode,
        weak_topics: weak,
      });
      timerOffset.current = Date.now() - Date.parse(a.server_time);
      autoSubmit.current = false;
      setAttempt(a);
      setIdx(0);
      setFeedback(null);
      setStartDialog(false);
      setPage("Test");
    });
  }
  async function startCustomPractice() {
    await act(async () => {
      if (!needAccount()) return;
      const a = await api("/attempts", "POST", {
        config_id: "quick",
        mode: "PRACTICE",
        subject: pSubject || undefined,
        topics: pTopic ? [pTopic] : undefined,
        difficulty: pDifficulty || undefined,
        source_type: pSource || undefined,
        count: pCount,
      });
      timerOffset.current = Date.now() - Date.parse(a.server_time);
      autoSubmit.current = false;
      setAttempt(a);
      setIdx(0);
      setFeedback(null);
      setPage("Test");
    });
  }
  function samplePractice() {
    const qs = [
      seed.find((q) => q.topic === "Transformers")!,
      seed.find((q) => q.topic === "Number Systems")!,
      seed.find((q) => q.topic === "Simple Interest")!,
      seed.find((q) => q.topic === "Directions")!,
      seed.find((q) => q.topic === "Indian Polity")!,
      seed.find((q) => q.topic === "Communication Systems")!,
      seed.find((q) => q.topic === "Networking")!,
      seed.find((q) => q.topic === "Algebra")!,
      seed.find((q) => q.topic === "Ranking")!,
      seed.find((q) => q.topic === "General Science")!,
    ];
    setAttempt({
      id: "preview",
      preview: true,
      name: "Sample practice",
      mode: "PRACTICE",
      status: "IN_PROGRESS",
      questions: qs,
      answers: {},
      started_at: new Date().toISOString(),
      deadline: new Date(Date.now() + 600000).toISOString(),
      policy: { correct_marks: 1, wrong_penalty: 1 / 3, duration_seconds: 600 },
    });
    setIdx(0);
    setFeedback(null);
    timerOffset.current = 0;
    autoSubmit.current = false;
    setPage("Test");
  }
  async function resume(id: string) {
    await act(async () => {
      const a = await api("/attempts/" + id);
      timerOffset.current = Date.now() - Date.parse(a.server_time);
      autoSubmit.current = false;
      setAttempt(a);
      setIdx(0);
      setFeedback(null);
      setPage(a.status === "SUBMITTED" ? "Results" : "Test");
    });
  }
  const submit = useCallback(async () => {
    if (!attempt) return;
    setBusy(true);
    try {
      if (attempt.preview) {
        let correct = 0,
          wrong = 0;
        const subj: Any = {},
          topics: Any = {};
        const review = attempt.questions.map((q: Question) => {
          const selected = attempt.answers[q.id]?.selected;
          const ok = selected === q.correct_option;
          if (selected) {
            if (ok) correct++;
            else wrong++;
          }
          for (const [group, key] of [
            [subj, q.subject],
            [topics, q.topic],
          ] as [Any, string][]) {
            const s = (group[key] ??= {
              total: 0,
              attempted: 0,
              correct: 0,
              wrong: 0,
            });
            s.total++;
            if (selected) {
              s.attempted++;
              s.correct += ok ? 1 : 0;
              s.wrong += ok ? 0 : 1;
            }
            s.accuracy = s.attempted ? (100 * s.correct) / s.attempted : 0;
          }
          return { ...q, selected, is_correct: ok };
        });
        const n = attempt.questions.length;
        const result = {
          total: n,
          attempted: correct + wrong,
          correct,
          wrong,
          unanswered: n - correct - wrong,
          score: Math.round((correct - wrong / 3) * 100) / 100,
          accuracy: correct + wrong ? (100 * correct) / (correct + wrong) : 0,
          percentage: (100 * (correct - wrong / 3)) / n,
          time_used_seconds: Math.min(
            600,
            Math.round((Date.now() - Date.parse(attempt.started_at)) / 1000),
          ),
          subjects: subj,
          topics,
          review,
        };
        setAttempt({ ...attempt, status: "SUBMITTED", result });
      } else {
        setAttempt(await api("/attempts/" + attempt.id + "/submit", "POST"));
        await refresh();
      }
      setPage("Results");
      setConfirmSubmit(false);
    } catch (e) {
      autoSubmit.current = false;
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [attempt, refresh]);
  useEffect(() => {
    if (page !== "Test" || !attempt || attempt.status !== "IN_PROGRESS") return;
    const tick = () => {
      const secs = Math.max(
        0,
        Math.ceil(
          (Date.parse(attempt.deadline) - (Date.now() - timerOffset.current)) /
            1000,
        ),
      );
      setRemaining(secs);
      if (secs === 0 && !autoSubmit.current && !saving.current) {
        autoSubmit.current = true;
        void submit();
      }
    };
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [attempt, page, submit]);
  useEffect(() => {
    if (page !== "Test") return;
    const f = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", f);
    return () => window.removeEventListener("beforeunload", f);
  }, [page]);
  async function saveAnswer(selected: string | null, marked?: boolean) {
    if (!attempt || saving.current) return;
    saving.current = true;
    setBusy(true);
    const q = attempt.questions[idx],
      old = attempt.answers[q.id] || {};
    const data = { selected, marked: marked ?? old.marked ?? false };
    try {
      if (attempt.preview) {
        setAttempt({
          ...attempt,
          answers: { ...attempt.answers, [q.id]: { ...data, visited: true } },
        });
        const previewFeedback = selected
          ? {
              correct: selected === q.correct_option,
              correct_option: q.correct_option,
              explanation: q.explanation,
              selected,
            }
          : null;
        setFeedback(previewFeedback);
        setFeedbackHistory((h) =>
          previewFeedback
            ? { ...h, [q.id]: previewFeedback }
            : (({ [q.id]: _drop, ...rest }) => rest)(h),
        );
      } else {
        const r = await api(
          `/attempts/${attempt.id}/answers/${q.id}`,
          "PUT",
          data,
        );
        if (r.expired) {
          setAttempt({ ...attempt, status: "SUBMITTED", result: r.result });
          setPage("Results");
        } else {
          setAttempt({
            ...attempt,
            answers: { ...attempt.answers, [q.id]: r.answer },
          });
          setFeedback(r.feedback);
          setFeedbackHistory((h) =>
            r.feedback
              ? { ...h, [q.id]: r.feedback }
              : (({ [q.id]: _drop, ...rest }) => rest)(h),
          );
        }
      }
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }
  async function goQuestion(n: number) {
    if (busy || !attempt) return;
    setIdx(n);
    const qid = attempt.questions[n]?.id;
    setFeedback((qid && feedbackHistory[qid]) || null);
  }
  async function authSubmit() {
    await act(async () => {
      if (!connected) throw Error("Connect your backend first");
      const r = await fetch(
        health.supabase_url +
          "/auth/v1/" +
          (signup ? "signup" : "token?grant_type=password"),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            apikey: health.supabase_anon_key,
          },
          body: JSON.stringify({
            email,
            password,
            ...(signup ? { data: { name: profileName || "Learner" } } : {}),
          }),
        },
      );
      const data: any = await r.json();
      if (!r.ok)
        throw Error(data.msg || data.error_description || "Sign-in failed");
      if (!data.access_token) {
        toast.success("Check your email to confirm your account.");
        return;
      }
      setToken(data.access_token);
      const u = await api("/me");
      setMe(u);
      setProfileDraft(u.name);
      setLogin(false);
      setPassword("");
      await refresh();
      toast.success("Signed in");
    });
  }
  async function reviewQuestion(q: Question, decision: string) {
    await act(async () => {
      await api("/questions/" + q.id + "/review", "POST", {
        status: decision,
        notes: reviewNotes,
        verified_pyq: verifyPyq,
      });
      setPreview(null);
      setReviewNotes("");
      setVerifyPyq(false);
      await loadBank();
      await refresh();
      toast.success("Review saved");
    });
  }
  function draft(q?: Question) {
    const fields = [
      "question_text",
      "option_a",
      "option_b",
      "option_c",
      "option_d",
      "correct_option",
      "explanation",
      "concept",
      "formula",
      "given",
      "calculation",
      "final_answer",
      "why_correct",
      "why_wrong",
      "subject",
      "topic",
      "subtopic",
      "difficulty",
      "source_type",
      "source_reference",
      "exam",
      "exam_year",
      "shift",
      "parent_question_id",
    ];
    setEditor(
      q
        ? Object.fromEntries(
            ["id", ...fields].map((k) => [
              k,
              q[k] ??
                (k === "exam_year" ||
                k === "parent_question_id" ||
                k === "why_wrong"
                  ? null
                  : ""),
            ]),
          )
        : {
            question_text: "",
            option_a: "",
            option_b: "",
            option_c: "",
            option_d: "",
            correct_option: "A",
            explanation: "",
            concept: "",
            formula: "",
            given: "",
            calculation: "",
            final_answer: "",
            why_correct: "",
            why_wrong: null,
            subject: subjects[0],
            topic: "",
            subtopic: "",
            difficulty: "Medium",
            source_type: "ORIGINAL",
            source_reference: "",
            exam: "RRB Technician Grade-I Signal",
            exam_year: null,
            shift: "",
            parent_question_id: null,
          },
    );
    setPreview(null);
  }
  async function saveQuestion() {
    await act(async () => {
      const { id, ...data } = editor!;
      await api("/questions" + (id ? "/" + id : ""), id ? "PUT" : "POST", data);
      setEditor(null);
      await loadBank();
      await refresh();
      toast.success("Draft saved for review");
    });
  }
  function variations(q: Question, difficulty?: string) {
    setGen({
      ...gen,
      subject: q.subject,
      topic: q.topic,
      subtopic: q.subtopic,
      difficulty: difficulty || q.difficulty,
      parent_question_id: q.id,
      source_type: q.source_type === "PYQ" ? "PYQ_PATTERN" : "ORIGINAL",
      concept: q.topic,
    });
    setPreview(null);
    navigate("AI Generator");
  }
  useEffect(() => {
    const context = (document as any).modelContext;
    if (!context?.registerTool) return;
    const life = new AbortController();
    Promise.resolve(
      context.registerTool(
        {
          name: "search_question_bank",
          description:
            "Open the question bank and filter original or approved questions by text.",
          inputSchema: {
            type: "object",
            properties: { query: { type: "string", maxLength: 200 } },
            required: ["query"],
            additionalProperties: false,
          },
          annotations: { readOnlyHint: true },
          execute: async (input: Any) => {
            if (typeof input.query !== "string" || input.query.length > 200)
              throw Error("query must be a string of at most 200 characters");
            setPage("Question Bank");
            setSearch(input.query);
            return { view: "Question Bank", query: input.query };
          },
        },
        { signal: life.signal },
      ),
    ).catch(() => {});
    return () => life.abort();
  }, []);
  const nav = [
    ["Dashboard", LayoutDashboard],
    ["Mock Tests", ClipboardList],
    ["Question Bank", BookOpen],
    ["Exam Preparation", BookOpen],
    ["Performance", ChartNoAxesCombined],
    ["Bookmarks", Bookmark],
  ] as const;
  const active = attempts.filter((a) => a.status === "IN_PROGRESS");
  const result = attempt?.result;
  return (
    <SidebarProvider>
      <Toaster richColors position="top-right" />
      <Sidebar className="app-sidebar">
        <SidebarHeader>
          <button className="brand" onClick={() => navigate("Dashboard")}>
            <span className="brand-icon">
              <Signal size={24} />
            </span>
            <span>
              Signal<span className="brand-light">Prep</span>
              <small>RRB TECHNICIAN · GRADE I</small>
            </span>
          </button>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <p className="nav-label">YOUR WORKSPACE</p>
            <SidebarMenu>
              {nav.map(([p, Icon]) => (
                <SidebarMenuItem key={p}>
                  <SidebarMenuButton
                    isActive={page === p}
                    onClick={() => navigate(p)}
                  >
                    <Icon />
                    <span>{p}</span>
                    {p === "Question Bank" && (
                      <span className="nav-count">{stats.total}</span>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
          <SidebarGroup>
            <p className="nav-label">QUESTION STUDIO</p>
            <SidebarMenu>
              {[
                ["AI Generator", Sparkles],
                ["Admin Review", ShieldCheck],
              ].map(([p, Icon]) => {
                const I = Icon as React.ElementType;
                return (
                  <SidebarMenuItem key={String(p)}>
                    <SidebarMenuButton
                      isActive={page === p}
                      onClick={() => navigate(String(p))}
                    >
                      <I />
                      <span>{String(p)}</span>
                      {p === "AI Generator" && (
                        <span className="tiny-new">AI</span>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroup>
          <div className="sidebar-tip">
            <div className="tiny-icon">
              <Zap size={19} />
            </div>
            <strong>A little practice. Every day.</strong>
            <p>Build understanding, one question at a time.</p>
            <button
              onClick={() =>
                connected && me
                  ? openStart("PRACTICE", "quick")
                  : samplePractice()
              }
            >
              Start a quick practice <ArrowUpRight size={16} />
            </button>
          </div>
        </SidebarContent>
        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton onClick={() => setSettings(true)}>
                <Settings />
                <span>Settings & connection</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
          <button
            className="profile"
            onClick={() =>
              me
                ? setSettings(true)
                : connected
                  ? setLogin(true)
                  : setSettings(true)
            }
          >
            <span className="avatar">
              {me ? (me.name || "L").slice(0, 2).toUpperCase() : "SP"}
            </span>
            <span>
              <b>{me?.name || "Your preparation space"}</b>
              <small>
                {me
                  ? me.role === "admin"
                    ? "Administrator"
                    : "Learner"
                  : "Preview · No account connected"}
              </small>
            </span>
            <ChevronRight size={16} />
          </button>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="topbar">
          <div>
            <SidebarTrigger />
            <span className="breadcrumb">
              Workspace <ChevronRight size={14} /> <strong>{page}</strong>
            </span>
          </div>
          <div>
            <span className="exam-chip">RRB Technician Grade-I Signal</span>
            <button
              className="icon-btn"
              aria-label="Toggle color theme"
              onClick={() => {
                setDark(!dark);
                document.documentElement.classList.toggle("dark", !dark);
                localStorage.setItem(
                  "signalprep-theme",
                  !dark ? "dark" : "light",
                );
              }}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>
        <main className={"main " + (page === "Test" ? "exam-main" : "")}>
          {(!connected || !me) && !loading && (
            <div className="connection-note">
              <span>
                <span className="status-dot" />
                {connected
                  ? "Sign in to save attempts and access your progress."
                  : "Preview workspace · Explore original questions. Connect your backend to save progress."}
              </span>
              <button
                onClick={() => (connected ? setLogin(true) : setSettings(true))}
              >
                {connected ? "Sign in" : "Connect backend"}{" "}
                <ArrowRight size={14} />
              </button>
            </div>
          )}
          {loading ? (
            <div className="loading">
              <LoaderCircle className="spin" />
              Opening your workspace…
            </div>
          ) : (
            <PageErrorBoundary onReset={() => navigate("Dashboard")}>
              {page === "Dashboard" && (
                <>
                  <div className="page-heading">
                    <div>
                      <p className="eyebrow">YOUR NEXT STEP STARTS HERE</p>
                      <h1>Make every question count.</h1>
                      <p>
                        A focused workspace for your Grade-I Signal preparation.
                      </p>
                    </div>
                    <button className="btn primary" onClick={() => openStart()}>
                      <Plus size={18} /> Generate mock test
                    </button>
                  </div>
                  <div className="stats-grid">
                    <Stat
                      icon={BookOpen}
                      label="Questions · includes basic practice"
                      value={stats.total}
                      foot={`${stats.topics} topics to explore`}
                    />
                    <Stat
                      icon={ClipboardList}
                      label="Tests completed"
                      value={analytics.completed || 0}
                      foot="Practice and exam attempts"
                    />
                    <Stat
                      icon={Target}
                      label="Exam accuracy"
                      value={
                        analytics.history.filter(
                          (a: Any) => a.mode === "EXAM" && a.exam_preparation,
                        ).length
                          ? Math.round(
                              analytics.history
                                .filter(
                                  (a: Any) =>
                                    a.mode === "EXAM" && a.exam_preparation,
                                )
                                .reduce(
                                  (n: number, a: Any) => n + a.accuracy,
                                  0,
                                ) /
                                analytics.history.filter(
                                  (a: Any) =>
                                    a.mode === "EXAM" && a.exam_preparation,
                                ).length,
                            ) + "%"
                          : "—"
                      }
                      foot="From your completed exam tests"
                    />
                    <Stat
                      icon={Zap}
                      label="Topics to strengthen"
                      value={analytics.weak_topics.length || "—"}
                      foot="Based on repeated exam results"
                    />
                  </div>
                  <div className="dashboard-grid">
                    <section className="mock-feature">
                      <div className="feature-top">
                        <Badge kind="mint">YOUR EXAM. YOUR PRACTICE.</Badge>
                        <span>01 / GRADE-I SIGNAL</span>
                      </div>
                      <h2>
                        Get exam-ready.
                        <br />
                        One mock at a time.
                      </h2>
                      <p>
                        A source-reviewed exam bank is required.
                        <br className="desktop" /> The 190 starter items are
                        basic practice.
                      </p>
                      <div className="feature-facts">
                        <span>
                          <b>100</b> questions
                        </span>
                        <span>
                          <b>90</b> minutes
                        </span>
                        <span>
                          <b>−⅓</b> wrong answer
                        </span>
                      </div>
                      <div className="feature-actions">
                        <button
                          className="btn mint-btn"
                          onClick={() => openStart("EXAM")}
                        >
                          Start exam mode <ArrowUpRight size={18} />
                        </button>
                        <button
                          className="text-link light"
                          onClick={() => openStart("PRACTICE")}
                        >
                          Practice with feedback <ArrowRight size={17} />
                        </button>
                      </div>
                      <div className="feature-bars" aria-hidden="true">
                        <i />
                        <i />
                        <i />
                        <i />
                        <i />
                      </div>
                    </section>
                    <section className="panel focus-panel">
                      <div className="section-top">
                        <h2>Your next focus</h2>
                        <Target size={20} />
                      </div>
                      <div className="focus-symbol">
                        <Target size={38} />
                      </div>
                      <h3>
                        {analytics.weak_topics.length
                          ? "Turn weak spots into strengths."
                          : "Find your starting point."}
                      </h3>
                      <p>
                        {analytics.weak_topics.length
                          ? analytics.weak_topics.join(", ")
                          : "Complete your first exam mock to see how you perform across subjects."}
                      </p>
                      <button
                        className="btn outline full"
                        onClick={() =>
                          analytics.weak_topics.length
                            ? openStart("PRACTICE", "grade1", true)
                            : openStart("EXAM")
                        }
                      >
                        {analytics.weak_topics.length
                          ? "Generate weak topic test"
                          : "Take a baseline mock"}
                        <ArrowRight size={16} />
                      </button>
                      <small>
                        Weak topics use at least 5 answers across 2 exams.
                      </small>
                    </section>
                  </div>
                  <section className="subject-section">
                    <div className="section-top">
                      <div>
                        <h2>Build a stronger foundation</h2>
                        <p>Explore the five subjects in your test pattern.</p>
                      </div>
                      <button
                        className="text-link"
                        onClick={() => navigate("Question Bank")}
                      >
                        View question bank <ArrowRight size={16} />
                      </button>
                    </div>
                    <div className="subject-grid">
                      {subjects.map((s, i) => {
                        const Icon = icons[i];
                        return (
                          <button
                            className={"subject-card color-" + i}
                            key={s}
                            onClick={() => {
                              navigate("Question Bank");
                              setSubject(s);
                            }}
                          >
                            <span className="subject-icon">
                              <Icon size={22} />
                            </span>
                            <h3>{s}</h3>
                            <span>
                              {stats.subjects[s] || 0} questions{" "}
                              <ChevronRight size={16} />
                            </span>
                            <div className="subject-rule" />
                            <small>
                              {distribution[i]} questions in full mock
                            </small>
                          </button>
                        );
                      })}
                    </div>
                  </section>
                  <div className="bottom-grid">
                    <section className="panel">
                      <div className="section-top">
                        <h2>Recent activity</h2>
                        <button
                          className="text-link"
                          onClick={() => navigate("Performance")}
                        >
                          View history <ArrowRight size={15} />
                        </button>
                      </div>
                      {active.length > 0 ? (
                        active.slice(0, 2).map((a) => (
                          <button
                            className="history-row"
                            key={a.id}
                            onClick={() => resume(a.id)}
                          >
                            <span className="subject-icon">
                              <Play size={18} />
                            </span>
                            <span>
                              <b>{a.name}</b>
                              <small>
                                In progress · {a.mode.toLowerCase()}
                              </small>
                            </span>
                            <Badge kind="amber">Resume</Badge>
                          </button>
                        ))
                      ) : analytics.history.length ? (
                        analytics.history.slice(0, 2).map((a: Any) => (
                          <button
                            className="history-row"
                            key={a.id}
                            onClick={() => resume(a.id)}
                          >
                            <ClipboardList size={22} />
                            <span>
                              <b>{a.name}</b>
                              <small>
                                {new Date(a.started_at).toLocaleDateString()} ·{" "}
                                {a.mode.toLowerCase()}
                              </small>
                            </span>
                            <strong>
                              {a.score}/{a.total}
                            </strong>
                          </button>
                        ))
                      ) : (
                        <div className="activity-empty">
                          <span className="subject-icon">
                            <ClipboardList size={24} />
                          </span>
                          <div>
                            <h3>Your first attempt belongs here.</h3>
                            <p>
                              Start a mock and create a record of your progress.
                            </p>
                          </div>
                        </div>
                      )}
                    </section>
                    <section className="source-note">
                      <ShieldCheck size={26} />
                      <div>
                        <h3>Know where your questions come from.</h3>
                        <p>
                          Every question is labelled. This starter bank contains
                          original educational questions; no question is
                          presented as a verified PYQ.
                        </p>
                        <button
                          className="text-link"
                          onClick={() => {
                            navigate("Question Bank");
                            setSource("ORIGINAL");
                          }}
                        >
                          Explore original questions <ArrowRight size={14} />
                        </button>
                      </div>
                    </section>
                  </div>
                </>
              )}
              {page === "Exam Preparation" && (
                <Preparation
                  connected={connected}
                  admin={me?.role === "admin"}
                  onStart={(id: string) => openStart("PRACTICE", id)}
                />
              )}
              {page === "Mock Tests" && (
                <>
                  <PageTitle
                    title="Train like it’s test day."
                    text="Choose instant feedback or a focused examination."
                  />
                  <div className="mode-grid">
                    {["PRACTICE", "EXAM"].map((m, i) => (
                      <section
                        className={"panel mode-card " + (i ? "exam-card" : "")}
                        key={m}
                      >
                        {i ? <Clock size={30} /> : <BookOpen size={30} />}
                        <Badge kind={i ? "mint" : "teal"}>
                          {i ? "TEST YOUR READINESS" : "LEARN AS YOU GO"}
                        </Badge>
                        <h2>{i ? "Exam mode" : "Practice mode"}</h2>
                        <p>
                          {i
                            ? "Verified PYQs and reviewed hard patterns. No reuse across your saved attempts. Requires sufficient approved material."
                            : "Get the correct answer and a worked explanation immediately after each selection."}
                        </p>
                        <ul>
                          <li>
                            <Check size={16} />
                            100 questions · 90 minutes
                          </li>
                          <li>
                            <Check size={16} />
                            Mark for review and question palette
                          </li>
                          <li>
                            <Check size={16} />
                            +1 correct · −⅓ wrong · 0 unanswered
                          </li>
                        </ul>
                        <button
                          className={"btn " + (i ? "mint-btn" : "primary")}
                          onClick={() => openStart(m)}
                        >
                          Generate {i ? "exam" : "practice"} test{" "}
                          <ArrowRight size={18} />
                        </button>
                      </section>
                    ))}
                  </div>
                  <section className="panel quick-row">
                    <div>
                      <h2>Have ten minutes?</h2>
                      <p>
                        {connected && me
                          ? "Try a short, saved test from the question bank."
                          : "Try 10 sample questions. This preview is temporary and is not saved."}
                      </p>
                    </div>
                    <button
                      className="btn outline"
                      onClick={() =>
                        connected && me
                          ? openStart("PRACTICE", "quick")
                          : samplePractice()
                      }
                    >
                      <Zap size={18} />
                      Quick practice
                    </button>
                  </section>
                  {connected && me && (
                    <section className="panel custom-practice">
                      <h2>Custom practice</h2>
                      <p>
                        Pick a subject, topic and difficulty to build your own
                        practice set with immediate feedback.
                      </p>
                      <div className="custom-practice-fields">
                        <Pick
                          label="Subject"
                          value={pSubject}
                          onChange={(v) => {
                            setPSubject(v);
                            setPTopic("");
                          }}
                          items={["", ...subjects]}
                        />
                        <Pick
                          label="Topic"
                          value={pTopic}
                          onChange={setPTopic}
                          items={["", ...(topicsBySubject[pSubject] || [])]}
                        />
                        <Pick
                          label="Difficulty"
                          value={pDifficulty}
                          onChange={setPDifficulty}
                          items={["", "Easy", "Medium", "Hard"]}
                        />
                        <Pick
                          label="Question type"
                          value={pSource}
                          onChange={setPSource}
                          items={["", "PYQ", "PYQ_PATTERN", "ORIGINAL"]}
                        />
                        <input
                          type="number"
                          min={1}
                          max={100}
                          value={pCount}
                          onChange={(e) =>
                            setPCount(
                              Math.max(1, Math.min(100, Number(e.target.value))),
                            )
                          }
                          aria-label="Number of questions"
                        />
                      </div>
                      <button
                        className="btn primary"
                        disabled={busy}
                        onClick={() => void startCustomPractice()}
                      >
                        Start custom practice <ArrowRight size={16} />
                      </button>
                    </section>
                  )}
                  {active.map((a) => (
                    <button
                      key={a.id}
                      className="history-row panel"
                      onClick={() => resume(a.id)}
                    >
                      <Play />
                      <span>
                        <b>{a.name}</b>
                        <small>Continue your saved attempt</small>
                      </span>
                      <ArrowRight />
                    </button>
                  ))}
                </>
              )}
              {["Question Bank", "Bookmarks", "Admin Review"].includes(
                page,
              ) && (
                <>
                  <div className="page-heading">
                    <div>
                      <p className="eyebrow">
                        {page === "Admin Review"
                          ? "QUALITY BEFORE QUANTITY"
                          : "YOUR LEARNING LIBRARY"}
                      </p>
                      <h1>
                        {page === "Bookmarks"
                          ? "Keep the useful ones close."
                          : page === "Admin Review"
                            ? "Review before release."
                            : "The question bank."}
                      </h1>
                      <p>
                        {page === "Admin Review"
                          ? "Verify the answer, explanation and source before approving a draft."
                          : `${bank.total} ${page === "Bookmarks" ? "bookmarked" : "available"} questions · Clear sources. Focused concepts.`}
                      </p>
                    </div>
                    {me?.role === "admin" && (
                      <div className="button-row">
                        <label className="btn outline">
                          <Upload size={17} />
                          Import CSV
                          <input
                            type="file"
                            accept=".csv"
                            hidden
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              if (f)
                                void act(async () => {
                                  const form = new FormData();
                                  form.append("file", f);
                                  setImportResult(
                                    await api("/import", "POST", form),
                                  );
                                  await loadBank();
                                  await refresh();
                                });
                              e.target.value = "";
                            }}
                          />
                        </label>
                        <button className="btn primary" onClick={() => draft()}>
                          <Plus size={17} />
                          Add question
                        </button>
                      </div>
                    )}
                  </div>
                  {page === "Admin Review" && me?.role !== "admin" ? (
                    <AccessPanel
                      connected={connected}
                      onConnect={() => setSettings(true)}
                      onLogin={() => setLogin(true)}
                    />
                  ) : (
                    <>
                      <div className="bank-toolbar">
                        <div className="search-box">
                          <Search size={18} />
                          <input
                            placeholder="Search a question or concept…"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                          />
                        </div>
                        <Pick
                          label="All subjects"
                          value={subject}
                          onChange={setSubject}
                          items={["", ...subjects]}
                        />
                        <Pick
                          label="All difficulties"
                          value={difficulty}
                          onChange={setDifficulty}
                          items={["", "Easy", "Medium", "Hard"]}
                        />
                        <Pick
                          label="All sources"
                          value={source}
                          onChange={setSource}
                          items={[
                            "",
                            "PYQ",
                            "PYQ_PATTERN",
                            "SUPPLEMENTARY",
                            "ORIGINAL",
                          ]}
                        />
                      </div>
                      <div className="filter-secondary">
                        <input
                          aria-label="Filter by topic"
                          placeholder="Filter by topic"
                          value={topic}
                          onChange={(e) => setTopic(e.target.value)}
                        />
                        <input
                          aria-label="Filter by exam year"
                          type="number"
                          placeholder="Exam year"
                          value={year}
                          onChange={(e) => setYear(e.target.value)}
                        />
                        {me?.role === "admin" && page !== "Admin Review" && (
                          <Pick
                            label="All statuses"
                            value={status}
                            onChange={setStatus}
                            items={[
                              "",
                              "ACTIVE",
                              "PENDING_REVIEW",
                              "REJECTED",
                              "ARCHIVED",
                            ]}
                          />
                        )}
                        <span>
                          {stats.sources.PYQ || 0} PYQs ·{" "}
                          {stats.sources.PYQ_PATTERN || 0} pattern ·{" "}
                          {stats.sources.ORIGINAL || 0} original
                        </span>
                      </div>
                      {bank.items.length ? (
                        <div className="question-list">
                          {bank.items.map((q: Question, i: number) => (
                            <article className="bank-question panel" key={q.id}>
                              <span className="question-number">
                                {String((bankPage - 1) * 25 + i + 1).padStart(
                                  2,
                                  "0",
                                )}
                              </span>
                              <div>
                                <div className="question-meta">
                                  <span>{q.subject}</span>
                                  <span> / </span>
                                  <span>{q.topic}</span>
                                  <Badge kind="teal">
                                    {q.source_type.replace("_", " ")}
                                  </Badge>
                                  <Badge
                                    kind={
                                      q.difficulty === "Hard"
                                        ? "amber"
                                        : "neutral"
                                    }
                                  >
                                    {q.difficulty}
                                  </Badge>
                                  {me?.role === "admin" && (
                                    <Badge>{q.status}</Badge>
                                  )}
                                </div>
                                <button
                                  className="question-title"
                                  onClick={() => {
                                    setPreview(q);
                                    setReveal(false);
                                  }}
                                >
                                  {q.question_text}
                                </button>
                                <p>{q.subtopic || q.topic}</p>
                              </div>
                              <button
                                className="icon-btn"
                                aria-label="Bookmark question"
                                onClick={() =>
                                  void act(async () => {
                                    if (!needAccount()) return;
                                    await api(
                                      "/questions/" + q.id + "/bookmark",
                                      "POST",
                                    );
                                    await loadBank();
                                    toast.success(
                                      q.bookmarked
                                        ? "Bookmark removed"
                                        : "Question bookmarked",
                                    );
                                  })
                                }
                              >
                                <Bookmark
                                  size={19}
                                  fill={q.bookmarked ? "currentColor" : "none"}
                                />
                              </button>
                              <button
                                className="icon-btn"
                                aria-label="Preview question"
                                onClick={() => {
                                  setPreview(q);
                                  setReveal(false);
                                }}
                              >
                                <ArrowUpRight size={19} />
                              </button>
                            </article>
                          ))}
                        </div>
                      ) : (
                        <Empty
                          title={
                            page === "Bookmarks"
                              ? "No bookmarks yet."
                              : page === "Admin Review"
                                ? "No questions awaiting review."
                                : "No questions match."
                          }
                        >
                          {page === "Bookmarks"
                            ? "Bookmark questions from the bank after connecting your account."
                            : "Try another filter or add a question to the bank."}
                        </Empty>
                      )}
                      <div className="pagination">
                        <span>
                          Page {bankPage} of {bank.pages}
                        </span>
                        <button
                          className="btn outline"
                          disabled={bankPage === 1}
                          onClick={() => setBankPage(bankPage - 1)}
                        >
                          <ChevronLeft size={16} />
                          Previous
                        </button>
                        <button
                          className="btn outline"
                          disabled={bankPage >= bank.pages}
                          onClick={() => setBankPage(bankPage + 1)}
                        >
                          Next
                          <ChevronRight size={16} />
                        </button>
                      </div>
                    </>
                  )}
                </>
              )}
              {page === "Performance" && (
                <>
                  <PageTitle
                    title="See what’s getting stronger."
                    text="Exam results measure readiness. Practice attempts help you learn."
                  />
                  <div className="stats-grid">
                    <Stat
                      icon={ClipboardList}
                      label="Completed attempts"
                      value={analytics.completed}
                      foot="All saved tests"
                    />
                    <Stat
                      icon={ShieldCheck}
                      label="Exam attempts"
                      value={analytics.exam_completed || 0}
                      foot="Used in readiness analytics"
                    />
                    <Stat
                      icon={Target}
                      label="Topics tested"
                      value={Object.keys(analytics.topics).length}
                      foot="From submitted exam answers"
                    />
                    <Stat
                      icon={Zap}
                      label="Weak topics"
                      value={analytics.weak_topics.length}
                      foot="Below 60% across repeated exams"
                    />
                  </div>
                  <Tabs defaultValue="subjects">
                    <TabsList>
                      <TabsTrigger value="subjects">
                        Subject performance
                      </TabsTrigger>
                      <TabsTrigger value="topics">Topic breakdown</TabsTrigger>
                      <TabsTrigger value="history">Test history</TabsTrigger>
                    </TabsList>
                    <TabsContent value="subjects">
                      <section className="panel performance-panel">
                        {Object.keys(analytics.subjects).length ? (
                          Object.entries(analytics.subjects).map(
                            ([name, v]: [string, any]) => (
                              <div className="performance-row" key={name}>
                                <div>
                                  <strong>{name}</strong>
                                  <span>
                                    {v.correct}/{v.attempted} correct
                                  </span>
                                </div>
                                <Progress value={v.accuracy} />
                                <b>{v.accuracy}%</b>
                              </div>
                            ),
                          )
                        ) : (
                          <Empty title="A clear picture starts with your first exam.">
                            Complete an exam mock to see subject performance
                            here.
                          </Empty>
                        )}
                      </section>
                    </TabsContent>
                    <TabsContent value="topics">
                      <section className="panel">
                        <PerformanceTable data={analytics.topics} />
                        {analytics.weak_topics.length > 0 && (
                          <button
                            className="btn primary"
                            onClick={() =>
                              openStart("PRACTICE", "grade1", true)
                            }
                          >
                            Generate weak topic test <ArrowRight size={16} />
                          </button>
                        )}
                      </section>
                    </TabsContent>
                    <TabsContent value="history">
                      <section className="panel">
                        {analytics.history.length ? (
                          analytics.history.map((a: Any) => (
                            <button
                              className="history-row"
                              key={a.id}
                              onClick={() => resume(a.id)}
                            >
                              <ClipboardList />
                              <span>
                                <b>{a.name}</b>
                                <small>
                                  {new Date(a.started_at).toLocaleString()} ·{" "}
                                  {a.mode}
                                </small>
                              </span>
                              <strong>
                                {a.score}/{a.total}
                              </strong>
                              <ChevronRight />
                            </button>
                          ))
                        ) : (
                          <Empty title="Your history will grow with you.">
                            Saved attempts appear here after submission.
                          </Empty>
                        )}
                      </section>
                    </TabsContent>
                  </Tabs>
                </>
              )}
              {page === "AI Generator" && (
                <>
                  <PageTitle
                    title="New questions. Same core concept."
                    text="Generate original drafts, check their reasoning, then review before publishing."
                  />
                  {me?.role !== "admin" ? (
                    <AccessPanel
                      connected={connected}
                      onConnect={() => setSettings(true)}
                      onLogin={() => setLogin(true)}
                    />
                  ) : (
                    <div className="generator-layout">
                      <section className="panel">
                        <div className="section-top">
                          <h2>Question generation brief</h2>
                          <Sparkles size={22} />
                        </div>
                        {!health.ai_enabled && (
                          <div className="notice">
                            <AlertCircle size={20} />
                            <p>
                              AI generation is disabled. Set AI_PROVIDER,
                              AI_MODEL and AI_API_KEY on your backend, then
                              restart it.
                            </p>
                          </div>
                        )}
                        <div className="form-grid">
                          <Field label="Subject">
                            <Pick
                              label="Subject"
                              value={gen.subject}
                              items={subjects}
                              onChange={(v) => setGen({ ...gen, subject: v })}
                            />
                          </Field>
                          <Field label="Topic">
                            <input
                              value={gen.topic}
                              onChange={(e) =>
                                setGen({ ...gen, topic: e.target.value })
                              }
                            />
                          </Field>
                          <Field label="Subtopic">
                            <input
                              value={gen.subtopic}
                              onChange={(e) =>
                                setGen({ ...gen, subtopic: e.target.value })
                              }
                            />
                          </Field>
                          <Field label="Difficulty">
                            <Pick
                              label="Difficulty"
                              value={gen.difficulty}
                              items={["Easy", "Medium", "Hard"]}
                              onChange={(v) =>
                                setGen({ ...gen, difficulty: v })
                              }
                            />
                          </Field>
                          <Field label="PYQ-pattern variation">
                            <Pick
                              label="Variation"
                              value={gen.variant_kind || "MATCHED"}
                              items={["MATCHED", "HARDER"]}
                              onChange={(v) =>
                                setGen({ ...gen, variant_kind: v })
                              }
                            />
                          </Field>
                          <Field label="Number of questions (1–20)">
                            <input
                              type="number"
                              min="1"
                              max="20"
                              value={gen.count}
                              onChange={(e) =>
                                setGen({
                                  ...gen,
                                  count: Number(e.target.value),
                                })
                              }
                            />
                          </Field>
                          <Field label="Source type">
                            <Pick
                              label="Source type"
                              value={gen.source_type}
                              items={["ORIGINAL", "PYQ_PATTERN"]}
                              onChange={(v) =>
                                setGen({ ...gen, source_type: v })
                              }
                            />
                          </Field>
                          <Field label="Parent question ID (optional)">
                            <input
                              value={gen.parent_question_id}
                              onChange={(e) =>
                                setGen({
                                  ...gen,
                                  parent_question_id: e.target.value,
                                })
                              }
                            />
                          </Field>
                          <Field label="Question style">
                            <input
                              value={gen.style}
                              onChange={(e) =>
                                setGen({ ...gen, style: e.target.value })
                              }
                            />
                          </Field>
                        </div>
                        <Field label="Concept / pattern reference">
                          <textarea
                            value={gen.concept}
                            placeholder="Describe the principle and the reasoning you want to test."
                            onChange={(e) =>
                              setGen({ ...gen, concept: e.target.value })
                            }
                          />
                        </Field>
                        <button
                          disabled={!health.ai_enabled || busy}
                          className="btn primary full"
                          onClick={() =>
                            void act(async () => {
                              await api("/generate", "POST", {
                                ...gen,
                                parent_question_id:
                                  gen.parent_question_id || null,
                              });
                              setJobs(await api("/jobs"));
                              await refresh();
                              toast.success(
                                "Drafts generated. Review them before approval.",
                              );
                            })
                          }
                        >
                          {busy ? (
                            <LoaderCircle className="spin" size={17} />
                          ) : (
                            <Sparkles size={17} />
                          )}
                          Generate questions
                        </button>
                      </section>
                      <div>
                        <section className="panel pipeline">
                          <h2>From concept to question bank</h2>
                          {[
                            "Extract concept & analyze pattern",
                            "Generate questions & explanations",
                            "Check arithmetic & answer consistency",
                            "Detect exact and near duplicates",
                            "Review and approve as administrator",
                          ].map((v, i) => (
                            <div key={v}>
                              <span>{i + 1}</span>
                              <p>{v}</p>
                            </div>
                          ))}
                          <p className="muted">
                            AI checks can miss mistakes. Formula validity,
                            ambiguity, source authenticity and difficulty still
                            require a human check.
                          </p>
                        </section>
                        <section className="panel">
                          <h2>Generation history</h2>
                          {jobs.length ? (
                            jobs.map((j) => (
                              <div className="job" key={j.id}>
                                <strong>{j.request.topic}</strong>
                                <Badge>{j.status}</Badge>
                                <p>
                                  {j.output.question_ids?.length || 0} draft
                                  questions ·{" "}
                                  {new Date(j.created_at).toLocaleDateString()}
                                </p>
                                {j.output.error && <p>{j.output.error}</p>}
                              </div>
                            ))
                          ) : (
                            <p className="muted">No generation jobs yet.</p>
                          )}
                          <button
                            className="text-link"
                            onClick={() => navigate("Admin Review")}
                          >
                            Open review queue <ArrowRight size={16} />
                          </button>
                        </section>
                      </div>
                    </div>
                  )}
                </>
              )}
              {page === "Test" && attempt && (
                <>
                  <div className="cbt-header">
                    <div>
                      <Badge kind="teal">
                        {attempt.mode} {attempt.preview ? "· PREVIEW" : ""}
                      </Badge>
                      <h1>{attempt.name}</h1>
                    </div>
                    <div
                      className={"timer " + (remaining < 300 ? "urgent" : "")}
                    >
                      <Clock size={22} />
                      <span>
                        <small>TIME REMAINING</small>
                        <b>
                          {String(Math.floor(remaining / 60)).padStart(2, "0")}:
                          {String(remaining % 60).padStart(2, "0")}
                        </b>
                      </span>
                    </div>
                  </div>
                  {attempt.preview && (
                    <div className="notice">
                      Temporary sample session · answers and results are not
                      saved.
                    </div>
                  )}
                  {remaining < 300 && (
                    <p className="time-warning" role="status">
                      Less than 5 minutes left. Your test submits automatically
                      when time ends.
                    </p>
                  )}
                  <div className="cbt-grid">
                    <section className="panel cbt-question">
                      <div className="section-top">
                        <span className="eyebrow">
                          QUESTION {idx + 1} OF {attempt.questions.length}
                        </span>
                        <Badge>{attempt.questions[idx].subject}</Badge>
                      </div>
                      <div className="question-meta">
                        <Badge kind="teal">
                          {attempt.questions[idx].source_type}
                        </Badge>
                        <span>{attempt.questions[idx].topic}</span>
                        <span>
                          +{attempt.policy.correct_marks} / −
                          {Number(attempt.policy.wrong_penalty).toFixed(2)}
                        </span>
                      </div>
                      <h2>{attempt.questions[idx].question_text}</h2>
                      <RadioGroup
                        key={attempt.questions[idx].id}
                        value={
                          attempt.answers[attempt.questions[idx].id]
                            ?.selected || ""
                        }
                        disabled={busy || remaining === 0}
                        onValueChange={(v) => void saveAnswer(v)}
                      >
                        {["A", "B", "C", "D"].map((k) => (
                          <label
                            key={k}
                            className={
                              "answer-option " +
                              (attempt.answers[attempt.questions[idx].id]
                                ?.selected === k
                                ? "selected"
                                : "")
                            }
                            htmlFor={"opt-" + k}
                          >
                            <RadioGroupItem value={k} id={"opt-" + k} />
                            <b>{k}</b>
                            <span>
                              {
                                attempt.questions[idx][
                                  "option_" + k.toLowerCase()
                                ]
                              }
                            </span>
                          </label>
                        ))}
                      </RadioGroup>
                      {feedback && (
                        <div
                          className={
                            "feedback " +
                            (feedback.correct ? "correct" : "wrong")
                          }
                        >
                          <h3>
                            {feedback.correct ? (
                              <CheckCircle2 size={20} />
                            ) : (
                              <X size={20} />
                            )}{" "}
                            {feedback.correct ? "Correct" : "Wrong"}
                          </h3>
                          <strong>
                            Correct answer: {feedback.correct_option}.{" "}
                            {
                              attempt.questions[idx][
                                "option_" +
                                  feedback.correct_option.toLowerCase()
                              ]
                            }
                          </strong>
                          <ExplanationBlock
                            data={feedback}
                            selected={feedback.selected}
                          />
                        </div>
                      )}
                      <div className="cbt-actions">
                        <button
                          className="btn outline"
                          disabled={idx === 0 || busy}
                          onClick={() => goQuestion(idx - 1)}
                        >
                          <ChevronLeft size={16} />
                          Previous
                        </button>
                        <button
                          className="btn outline"
                          disabled={busy}
                          onClick={() =>
                            saveAnswer(
                              attempt.answers[attempt.questions[idx].id]
                                ?.selected || null,
                              !attempt.answers[attempt.questions[idx].id]
                                ?.marked,
                            )
                          }
                        >
                          <Flag size={16} />
                          {attempt.answers[attempt.questions[idx].id]?.marked
                            ? "Unmark"
                            : "Mark for review"}
                        </button>
                        <button
                          className="text-link"
                          disabled={busy}
                          onClick={() => saveAnswer(null)}
                        >
                          Clear response
                        </button>
                        <button
                          className="btn primary"
                          disabled={busy}
                          onClick={() =>
                            idx + 1 < attempt.questions.length
                              ? goQuestion(idx + 1)
                              : setConfirmSubmit(true)
                          }
                        >
                          {busy
                            ? "Saving…"
                            : idx + 1 === attempt.questions.length
                              ? "Finish"
                              : "Save & Next"}
                          <ArrowRight size={16} />
                        </button>
                      </div>
                      <small className="muted">
                        Selections save immediately. Marked answers are included
                        in scoring.
                      </small>
                    </section>
                    <aside className="panel palette-panel">
                      <div className="section-top">
                        <h2>Question palette</h2>
                        <span>
                          {
                            Object.values(attempt.answers).filter(
                              (a: any) => a.selected,
                            ).length
                          }
                          /{attempt.questions.length}
                        </span>
                      </div>
                      <Progress
                        value={
                          (100 *
                            Object.values(attempt.answers).filter(
                              (a: any) => a.selected,
                            ).length) /
                          attempt.questions.length
                        }
                      />
                      {(() => {
                        let answered = 0,
                          marked = 0,
                          notAnswered = 0;
                        for (const q of attempt.questions as Question[]) {
                          const a = attempt.answers[q.id];
                          if (a?.selected) answered++;
                          else notAnswered++;
                          if (a?.marked) marked++;
                        }
                        return (
                          <div className="palette-counts">
                            <span>Answered: {answered}</span>
                            <span>Not answered: {notAnswered}</span>
                            <span>Marked: {marked}</span>
                          </div>
                        );
                      })()}
                      <div className="palette">
                        {attempt.questions.map((q: Question, i: number) => {
                          const a = attempt.answers[q.id];
                          return (
                            <button
                              aria-label={
                                "Question " +
                                (i + 1) +
                                (a?.marked ? ", marked" : "") +
                                (a?.selected ? ", answered" : ", not answered")
                              }
                              key={q.id}
                              disabled={busy}
                              className={
                                (a?.marked
                                  ? a.selected
                                    ? "answered-marked"
                                    : "marked"
                                  : a?.selected
                                    ? "answered"
                                    : "not-answered") +
                                (idx === i ? " current" : "")
                              }
                              onClick={() => goQuestion(i)}
                            >
                              {i + 1}
                            </button>
                          );
                        })}
                      </div>
                      <div className="palette-legend">
                        {[
                          ["answered", "Answered"],
                          ["not-answered", "Not answered"],
                          ["marked", "Marked for review"],
                          ["answered-marked", "Answered + marked"],
                        ].map(([c, v]) => (
                          <span key={c}>
                            <i className={c} />
                            {v}
                          </span>
                        ))}
                      </div>
                      <button
                        className="btn primary full"
                        disabled={busy}
                        onClick={() => setConfirmSubmit(true)}
                      >
                        Submit test <Check size={17} />
                      </button>
                    </aside>
                  </div>
                </>
              )}
              {page === "Results" && result && (
                <>
                  <div className="page-heading">
                    <div>
                      <p className="eyebrow">
                        {attempt?.preview
                          ? "TEMPORARY PREVIEW RESULT"
                          : attempt?.mode + " RESULT"}
                      </p>
                      <h1>A little more clarity. A better next step.</h1>
                      <p>
                        {attempt?.name} ·{" "}
                        {attempt?.mode === "PRACTICE"
                          ? "Practice scores may improve after viewing feedback."
                          : "Submitted exam attempt."}
                      </p>
                    </div>
                    <button className="btn primary" onClick={() => openStart()}>
                      Start another test <ArrowRight size={16} />
                    </button>
                  </div>
                  <div className="result-summary">
                    <div className="score-circle">
                      <strong>{result.score}</strong>
                      <span>out of {result.max_score || result.total}</span>
                    </div>
                    <div>
                      <h2>{Math.round(result.accuracy)}% accuracy</h2>
                      <p>
                        {result.correct} correct · {result.wrong} wrong ·{" "}
                        {result.unanswered} unanswered
                      </p>
                      {attempt?.policy && (
                        <p className="muted score-formula">
                          Score = {result.correct} × {attempt.policy.correct_marks}
                          {" − "}
                          {result.wrong} ×{" "}
                          {Number(attempt.policy.wrong_penalty).toFixed(2)} ={" "}
                          {result.score}
                        </p>
                      )}
                      <div className="result-meta">
                        <span>
                          {result.attempted}/{result.total} attempted
                        </span>
                        <span>
                          {Math.round(result.percentage * 10) / 10}% score
                        </span>
                        <span>
                          {Math.floor(result.time_used_seconds / 60)}m{" "}
                          {result.time_used_seconds % 60}s used
                        </span>
                      </div>
                    </div>
                  </div>
                  <Tabs defaultValue="breakdown">
                    <TabsList>
                      <TabsTrigger value="breakdown">
                        Subject & topic results
                      </TabsTrigger>
                      <TabsTrigger value="answers">Review answers</TabsTrigger>
                    </TabsList>
                    <TabsContent value="breakdown">
                      <div className="bottom-grid">
                        <section className="panel">
                          <h2>Subject performance</h2>
                          <PerformanceTable data={result.subjects} />
                        </section>
                        <section className="panel">
                          <h2>Topics to practise</h2>
                          <PerformanceTable data={result.topics} />
                          <p className="muted">
                            Topics below 60% accuracy are a starting point.
                            Repeated exam results determine your saved weak
                            topics.
                          </p>
                        </section>
                      </div>
                    </TabsContent>
                    <TabsContent value="answers">
                      {result.review.map((q: Any, i: number) => (
                        <section key={q.id} className="panel answer-review">
                          <div className="question-meta">
                            <Badge
                              kind={
                                q.selected
                                  ? q.is_correct
                                    ? "teal"
                                    : "red"
                                  : "neutral"
                              }
                            >
                              {q.selected
                                ? q.is_correct
                                  ? "Correct"
                                  : "Wrong"
                                : "Unanswered"}
                            </Badge>
                            <span>
                              {q.subject} / {q.topic}
                            </span>
                          </div>
                          {q.source_type === "PYQ" && (
                            <p className="muted source-line">
                              Verified PYQ · {q.exam} {q.exam_year}
                              {q.shift ? ` · ${q.shift}` : ""}
                            </p>
                          )}
                          {q.source_type === "PYQ_PATTERN" && (
                            <p className="muted source-line">
                              PYQ-pattern practice question — not an official
                              previous-year question
                            </p>
                          )}
                          <h3>
                            {i + 1}. {q.question_text}
                          </h3>
                          <p>
                            Your answer:{" "}
                            {q.selected
                              ? `${q.selected}. ${q["option_" + q.selected.toLowerCase()]}`
                              : "Not answered"}
                          </p>
                          <strong>
                            Correct: {q.correct_option}.{" "}
                            {q["option_" + q.correct_option.toLowerCase()]}
                          </strong>
                          <ExplanationBlock data={q} selected={q.selected} />
                        </section>
                      ))}
                    </TabsContent>
                  </Tabs>
                </>
              )}
            </PageErrorBoundary>
          )}
          <footer className="footer">
            <span>
              <Signal size={14} /> SignalPrep
            </span>
            <span>Basic practice + source-reviewed exam preparation.</span>
            <span>Study platform · Not affiliated with RRB</span>
          </footer>
        </main>
      </SidebarInset>
      <Dialog open={startDialog} onOpenChange={setStartDialog}>
        <DialogContent className="modal">
          <DialogHeader>
            <DialogTitle>
              Generate your {weak ? "weak topic " : ""}test
            </DialogTitle>
            <DialogDescription>
              Questions are selected from the active bank. Your order and
              scoring rules are saved with the attempt.
            </DialogDescription>
          </DialogHeader>
          <Field label="Test configuration">
            <Pick
              label="Configuration"
              value={configId}
              items={configs.map((c) => c.id)}
              onChange={setConfigId}
            />
          </Field>
          <p>{configs.find((c) => c.id === configId)?.name}</p>
          <Field label="Mode">
            <Pick
              label="Mode"
              value={mode}
              items={["PRACTICE", "EXAM"]}
              onChange={(v) => {
                setMode(v);
                setConfigId(v === "EXAM" ? "exam-prep" : "grade1");
              }}
            />
          </Field>
          <div className="notice">
            {mode === "PRACTICE"
              ? "Answers appear immediately after selecting an option."
              : "Answers remain hidden until submission."}
          </div>
          <p className="muted">
            The 190 starter questions are Basic Practice. Exam Preparation
            separates verified PYQs, original hard patterns and unverified
            supplementary examples. Its sessions exclude previous question IDs
            and simple numerical variants; insufficient stock blocks a test. See
            Exam Preparation for the official syllabus checklist, source
            evidence and remaining gaps.
          </p>
          <button
            className="btn primary full"
            disabled={busy}
            onClick={startTest}
          >
            {busy ? "Generating…" : "Generate & start test"}
            <ArrowRight size={17} />
          </button>
          {!connected && (
            <button
              className="text-link"
              onClick={() => {
                setStartDialog(false);
                samplePractice();
              }}
            >
              Try 10 temporary sample questions instead
            </button>
          )}
        </DialogContent>
      </Dialog>
      <Dialog open={settings} onOpenChange={setSettings}>
        <DialogContent className="modal wide-modal">
          <DialogHeader>
            <DialogTitle>Settings & connection</DialogTitle>
            <DialogDescription>
              Connect the FastAPI backend to enable accounts, persistent tests
              and admin workflows.
            </DialogDescription>
          </DialogHeader>
          <Badge kind={connected ? "teal" : "amber"}>
            {connected
              ? "Backend connected"
              : "Preview · Backend not connected"}
          </Badge>
          <Field label="Backend URL">
            <input
              placeholder="https://your-backend.example.com"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
            />
          </Field>
          <p className="muted">
            For Windows development use http://127.0.0.1:8000. Hosted
            deployments should use HTTPS. Leave blank to use the
            server-configured backend.
          </p>
          <button
            className="btn primary"
            disabled={busy}
            onClick={() =>
              void act(async () => {
                if (apiUrl) {
                  const u = new URL(apiUrl);
                  if (!["https:", "http:"].includes(u.protocol))
                    throw Error("Use an HTTP or HTTPS URL");
                  if (
                    u.protocol === "http:" &&
                    !["127.0.0.1", "localhost"].includes(u.hostname)
                  )
                    throw Error("Remote backend must use HTTPS");
                }
                configure(apiUrl);
                setMe(null);
                setAttempt(null);
                setPage("Dashboard");
                setStats(initialStats);
                setAnalytics({
                  history: [],
                  topics: {},
                  subjects: {},
                  weak_topics: [],
                  completed: 0,
                });
                setAttempts([]);
                await connect();
                const h = await api("/health");
                toast.success(
                  h.development_auth
                    ? "Connected to local development mode"
                    : "Backend connected. Sign in to continue.",
                );
              })
            }
          >
            Test & connect
          </button>
          {health.development_auth && connected && (
            <div className="notice">
              Local development mode uses a single administrator account. Do not
              expose this mode to the internet.
            </div>
          )}
          {me && (
            <>
              <Field label="Display name">
                <input
                  value={profileDraft}
                  onChange={(e) => setProfileDraft(e.target.value)}
                />
              </Field>
              <button
                className="btn outline"
                onClick={() =>
                  void act(async () => {
                    setMe(await api("/me", "PUT", { name: profileDraft }));
                    toast.success("Profile updated");
                  })
                }
              >
                Save profile
              </button>
              {!health.development_auth && (
                <button
                  className="text-link"
                  onClick={() => {
                    setToken("");
                    setMe(null);
                    setStats(initialStats);
                    setAnalytics({
                      history: [],
                      topics: {},
                      subjects: {},
                      weak_topics: [],
                      completed: 0,
                    });
                    setAttempts([]);
                    setAttempt(null);
                    setPage("Dashboard");
                    setSettings(false);
                  }}
                >
                  <LogOut size={16} />
                  Sign out
                </button>
              )}
            </>
          )}
          {me?.role === "admin" && (
            <details>
              <summary>Admin · Test configuration</summary>
              <Field label="New configuration ID">
                <input
                  placeholder="e.g. custom-20"
                  value={newConfigId}
                  onChange={(e) => setNewConfigId(e.target.value)}
                />
              </Field>
              <button
                className="btn outline"
                disabled={!newConfigId || busy}
                onClick={() =>
                  void act(async () => {
                    if (!/^[a-z0-9-]{3,50}$/.test(newConfigId))
                      throw Error(
                        "Use 3–50 lowercase letters, digits or hyphens",
                      );
                    if (configs.some((c) => c.id === newConfigId))
                      throw Error("That configuration already exists");
                    const { id, ...data } = configs.find(
                      (c) => c.id === configId,
                    )!;
                    await api("/configs/" + newConfigId, "PUT", {
                      ...data,
                      name: "Custom test · " + newConfigId,
                    });
                    await refresh();
                    setConfigId(newConfigId);
                    setNewConfigId("");
                    toast.success(
                      "Configuration created. Load and edit it below.",
                    );
                  })
                }
              >
                Create configuration from selected
              </button>
              <p className="muted">
                Edit subject counts, source/difficulty weights, scoring and
                question cooldown. The generator requires a feasible mix.
              </p>
              <Pick
                label="Configuration"
                value={configId}
                items={configs.map((c) => c.id)}
                onChange={(v) => {
                  setConfigId(v);
                  const { id, ...d } = configs.find((c) => c.id === v)!;
                  setConfigEdit(JSON.stringify(d, null, 2));
                }}
              />
              <button
                className="text-link"
                onClick={() => {
                  const { id, ...d } = configs.find((c) => c.id === configId)!;
                  setConfigEdit(JSON.stringify(d, null, 2));
                }}
              >
                Load configuration
              </button>
              <textarea
                className="code-input"
                aria-label="Test configuration JSON"
                value={configEdit}
                onChange={(e) => setConfigEdit(e.target.value)}
              />
              <button
                className="btn outline"
                disabled={!configEdit || busy}
                onClick={() =>
                  void act(async () => {
                    await api(
                      "/configs/" + configId,
                      "PUT",
                      JSON.parse(configEdit),
                    );
                    await refresh();
                    toast.success("Test configuration saved");
                  })
                }
              >
                Save configuration
              </button>
            </details>
          )}
        </DialogContent>
      </Dialog>
      <Dialog open={login} onOpenChange={setLogin}>
        <DialogContent className="modal">
          <DialogHeader>
            <DialogTitle>
              {signup ? "Create your account" : "Welcome back"}
            </DialogTitle>
            <DialogDescription>
              Sign in to save tests, bookmarks and progress.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void authSubmit();
            }}
          >
            {signup && (
              <Field label="Name">
                <input
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  required
                />
              </Field>
            )}
            <Field label="Email">
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Field>
            <Field label="Password">
              <input
                type="password"
                autoComplete={signup ? "new-password" : "current-password"}
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </Field>
            <button
              className="btn primary full"
              disabled={busy || !health.supabase_url}
            >
              {busy ? "Please wait…" : signup ? "Create account" : "Sign in"}
            </button>
          </form>
          <button className="text-link" onClick={() => setSignup(!signup)}>
            {signup
              ? "Already have an account? Sign in"
              : "New here? Create an account"}
          </button>
          <p className="muted">
            This app keeps your access token in memory. Sign in again after a
            page reload or session expiry.
          </p>
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!preview}
        onOpenChange={(v) => {
          if (!v) setPreview(null);
        }}
      >
        <DialogContent className="modal wide-modal">
          <DialogHeader>
            <DialogTitle>Question preview</DialogTitle>
            <DialogDescription>
              {preview?.subject} / {preview?.topic}
            </DialogDescription>
          </DialogHeader>
          {preview && (
            <>
              <div className="question-meta">
                <Badge kind="teal">{preview.source_type}</Badge>
                <Badge>{preview.difficulty}</Badge>
                <Badge>{preview.status}</Badge>
              </div>
              <h2>{preview.question_text}</h2>
              {["A", "B", "C", "D"].map((k) => (
                <div key={k} className="preview-option">
                  <b>{k}.</b> {String(preview["option_" + k.toLowerCase()])}
                </div>
              ))}
              {preview.correct_option && (reveal || me?.role === "admin") ? (
                <div className="feedback correct">
                  <strong>Answer: {preview.correct_option}</strong>
                  <ExplanationBlock data={preview} />
                </div>
              ) : preview.correct_option ? (
                <button className="btn outline" onClick={() => setReveal(true)}>
                  Show answer & explanation
                </button>
              ) : (
                <p className="muted">
                  Start a practice test to receive answer feedback.
                </p>
              )}
              <p className="muted">
                Verification: {String(preview.verification_status || "UNVERIFIED")}
                <br />
                Reference: {preview.source_reference || "No reference supplied"}
                {preview.parent_question_id && (
                  <>
                    <br />
                    Parent: {preview.parent_question_id}
                  </>
                )}
                <br />
                Question ID: {preview.id}
              </p>
              {me?.role === "admin" && connected && (
                <Field label="Map to official syllabus unit (select to save)">
                  <Pick
                    label="Syllabus unit"
                    value={
                      preview.generation_metadata?.syllabus_units?.[0] || ""
                    }
                    items={[
                      "",
                      ...preparationCatalog.units
                        .filter((u) => u.subject === preview.subject)
                        .map((u) => u.id),
                    ]}
                    onChange={async (value) => {
                      if (!value) return;
                      await act(async () => {
                        const q = await api(
                          `/questions/${preview.id}/syllabus`,
                          "PUT",
                          { unit_ids: [value] },
                        );
                        setPreview(q);
                      });
                    }}
                  />
                  <p className="muted">
                    {
                      preparationCatalog.units.find(
                        (u) =>
                          u.id ===
                          preview.generation_metadata?.syllabus_units?.[0],
                      )?.name
                    }
                  </p>
                </Field>
              )}
              {preview.generation_metadata && me?.role === "admin" && (
                <details>
                  <summary>Generation and quality checks</summary>
                  <pre>
                    {JSON.stringify(preview.generation_metadata, null, 2)}
                  </pre>
                </details>
              )}
              {me?.role === "admin" && (
                <>
                  <div className="button-row wrap">
                    <button
                      className="btn outline"
                      onClick={() => draft(preview)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn outline"
                      onClick={() =>
                        void act(async () => {
                          await api(
                            "/questions/" + preview.id + "/duplicate",
                            "POST",
                          );
                          setPreview(null);
                          await loadBank();
                          toast.success(
                            "Duplicate draft created. Rewrite before approval.",
                          );
                        })
                      }
                    >
                      Duplicate draft
                    </button>
                    <button
                      className="btn outline"
                      onClick={() => variations(preview)}
                    >
                      Regenerate / similar
                    </button>
                    <button
                      className="btn outline"
                      onClick={() => variations(preview, "Hard")}
                    >
                      Generate harder
                    </button>
                    <button
                      className="btn outline"
                      onClick={() => variations(preview, "Easy")}
                    >
                      Generate easier
                    </button>
                  </div>
                  <Field label="Review notes: paper, question ID, answer-key reference; for patterns, independent solution and difficulty rationale">
                    <textarea
                      value={reviewNotes}
                      onChange={(e) => setReviewNotes(e.target.value)}
                      placeholder="Explain how you checked the answer, source and explanation."
                    />
                  </Field>
                  {(preview.source_type === "PYQ" ||
                    preview.generation_metadata?.claimed_source_type ===
                      "PYQ") && (
                    <label className="checkbox-label">
                      <Checkbox
                        checked={verifyPyq}
                        onCheckedChange={(v) => setVerifyPyq(v === true)}
                      />
                      I independently verified this question against the cited
                      exam source.
                    </label>
                  )}
                  <div className="button-row">
                    <button
                      className="btn primary"
                      disabled={busy}
                      onClick={() => reviewQuestion(preview, "ACTIVE")}
                    >
                      <Check size={16} />
                      Approve
                    </button>
                    <button
                      className="btn outline"
                      disabled={busy}
                      onClick={() => reviewQuestion(preview, "REJECTED")}
                    >
                      Reject
                    </button>
                    <button
                      className="btn outline"
                      disabled={busy}
                      onClick={() => reviewQuestion(preview, "ARCHIVED")}
                    >
                      Archive
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!editor}
        onOpenChange={(v) => {
          if (!v) setEditor(null);
        }}
      >
        <DialogContent className="modal wide-modal">
          <DialogHeader>
            <DialogTitle>
              {editor?.id ? "Edit question" : "Add question"}
            </DialogTitle>
            <DialogDescription>
              All edits return a question to pending review. Existing attempts
              retain their original snapshot.
            </DialogDescription>
          </DialogHeader>
          {editor && (
            <>
              <Field label="Question">
                <textarea
                  value={editor.question_text}
                  onChange={(e) =>
                    setEditor({ ...editor, question_text: e.target.value })
                  }
                />
              </Field>
              <div className="form-grid">
                {["option_a", "option_b", "option_c", "option_d"].map((k) => (
                  <Field key={k} label={k.replace("_", " ").toUpperCase()}>
                    <input
                      value={editor[k]}
                      onChange={(e) =>
                        setEditor({ ...editor, [k]: e.target.value })
                      }
                    />
                  </Field>
                ))}
                {[
                  ["subject", subjects],
                  ["difficulty", ["Easy", "Medium", "Hard"]],
                  [
                    "source_type",
                    ["ORIGINAL", "PYQ_PATTERN", "SUPPLEMENTARY", "PYQ"],
                  ],
                  ["correct_option", ["A", "B", "C", "D"]],
                ].map(([k, items]) => (
                  <Field key={String(k)} label={String(k).replace("_", " ")}>
                    <Pick
                      label={String(k)}
                      value={editor[String(k)]}
                      items={items as string[]}
                      onChange={(v) => setEditor({ ...editor, [String(k)]: v })}
                    />
                  </Field>
                ))}
                {[
                  "topic",
                  "subtopic",
                  "source_reference",
                  "exam",
                  "shift",
                  "parent_question_id",
                ].map((k) => (
                  <Field key={k} label={k.replaceAll("_", " ")}>
                    <input
                      value={editor[k] || ""}
                      onChange={(e) =>
                        setEditor({
                          ...editor,
                          [k]:
                            e.target.value ||
                            (k === "parent_question_id" ? null : ""),
                        })
                      }
                    />
                  </Field>
                ))}
                <Field label="Exam year">
                  <input
                    type="number"
                    value={editor.exam_year || ""}
                    onChange={(e) =>
                      setEditor({
                        ...editor,
                        exam_year: e.target.value
                          ? Number(e.target.value)
                          : null,
                      })
                    }
                  />
                </Field>
              </div>
              <Field label="Explanation">
                <textarea
                  value={editor.explanation}
                  onChange={(e) =>
                    setEditor({ ...editor, explanation: e.target.value })
                  }
                />
              </Field>
              <p className="muted">
                Optional structured explanation — leave any of these blank
                for conceptual questions that don't need a formula or
                calculation.
              </p>
              <Field label="Concept">
                <textarea
                  value={editor.concept || ""}
                  onChange={(e) =>
                    setEditor({ ...editor, concept: e.target.value })
                  }
                />
              </Field>
              <Field label="Why correct">
                <textarea
                  value={editor.why_correct || ""}
                  onChange={(e) =>
                    setEditor({ ...editor, why_correct: e.target.value })
                  }
                />
              </Field>
              <div className="form-grid">
                <Field label="Formula">
                  <textarea
                    value={editor.formula || ""}
                    onChange={(e) =>
                      setEditor({ ...editor, formula: e.target.value })
                    }
                  />
                </Field>
                <Field label="Given">
                  <textarea
                    value={editor.given || ""}
                    onChange={(e) =>
                      setEditor({ ...editor, given: e.target.value })
                    }
                  />
                </Field>
              </div>
              <Field label="Calculation (step by step)">
                <textarea
                  value={editor.calculation || ""}
                  onChange={(e) =>
                    setEditor({ ...editor, calculation: e.target.value })
                  }
                />
              </Field>
              <Field label="Final answer">
                <input
                  value={editor.final_answer || ""}
                  onChange={(e) =>
                    setEditor({ ...editor, final_answer: e.target.value })
                  }
                />
              </Field>
              <Field label="Why each wrong option is wrong (one per line, e.g. A: reason)">
                <textarea
                  value={whyWrongToText(editor.why_wrong)}
                  onChange={(e) =>
                    setEditor({
                      ...editor,
                      why_wrong: textToWhyWrong(e.target.value),
                    })
                  }
                />
              </Field>
              <button
                className="btn primary"
                disabled={busy}
                onClick={saveQuestion}
              >
                Save for review
              </button>
            </>
          )}
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!importResult}
        onOpenChange={(v) => {
          if (!v) setImportResult(null);
        }}
      >
        <DialogContent className="modal">
          <DialogHeader>
            <DialogTitle>CSV import results</DialogTitle>
            <DialogDescription>
              Imported questions are pending review. None are automatically
              verified.
            </DialogDescription>
          </DialogHeader>
          {importResult && (
            <>
              <p>
                {importResult.imported} imported · {importResult.rejected}{" "}
                rejected ({importResult.duplicate} duplicates,{" "}
                {importResult.invalid} invalid)
              </p>
              <pre>{JSON.stringify(importResult.errors, null, 2)}</pre>
            </>
          )}
        </DialogContent>
      </Dialog>
      <AlertDialog open={confirmSubmit} onOpenChange={setConfirmSubmit}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit this test?</AlertDialogTitle>
            <AlertDialogDescription>
              {attempt
                ? attempt.questions.length -
                  Object.values(attempt.answers).filter((a: any) => a.selected)
                    .length
                : 0}{" "}
              questions remain unanswered. Marked answers count toward your
              score. Submission is final.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep working</AlertDialogCancel>
            <AlertDialogAction disabled={busy} onClick={() => void submit()}>
              Submit test
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SidebarProvider>
  );
}
function PageTitle({ title, text }: { title: string; text: string }) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
    </div>
  );
}
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
function PerformanceTable({ data }: { data: Any }) {
  return Object.keys(data).length ? (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Topic / subject</TableHead>
          <TableHead>Correct</TableHead>
          <TableHead>Accuracy</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Object.entries(data).map(([name, v]: [string, any]) => (
          <TableRow key={name}>
            <TableCell>{name}</TableCell>
            <TableCell>
              {v.correct}/{v.attempted}
            </TableCell>
            <TableCell>
              <Badge kind={v.accuracy >= 60 ? "teal" : "amber"}>
                {Math.round(v.accuracy)}%
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ) : (
    <Empty title="No exam data yet.">
      Complete an exam test to unlock this breakdown.
    </Empty>
  );
}
function AccessPanel({
  connected,
  onConnect,
  onLogin,
}: {
  connected: boolean;
  onConnect: () => void;
  onLogin: () => void;
}) {
  return (
    <section className="panel access-panel">
      <ShieldCheck size={40} />
      <h2>Administrator workspace</h2>
      <p>
        Question generation and review require an administrator account on a
        connected backend.
      </p>
      <button className="btn primary" onClick={connected ? onLogin : onConnect}>
        {connected ? "Sign in as administrator" : "Connect backend"}
        <ArrowRight size={16} />
      </button>
    </section>
  );
}

