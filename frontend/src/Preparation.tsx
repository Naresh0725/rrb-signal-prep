"use client";
import { useEffect, useState } from "react";
import { api } from "./api";
import catalog from "./preparation.json";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

type Any = Record<string, any>;
export default function Preparation({
  connected,
  admin,
  onStart,
}: {
  connected: boolean;
  admin: boolean;
  onStart: (id: string) => void;
}) {
  const [data, setData] = useState<Any | null>(null),
    [subject, setSubject] = useState("ALL"),
    [notes, setNotes] = useState<Record<string, string>>({}),
    [error, setError] = useState("");
  async function refresh() {
    try {
      setData(await api("/preparation"));
      setError("");
    } catch (e: any) {
      setError(e.message);
    }
  }
  useEffect(() => {
    if (connected) void refresh();
    else setData(null);
  }, [connected]);
  const units =
    data?.units ||
    catalog.units.map((u) => ({
      ...u,
      verified: null,
      patterns: null,
      supplementary: null,
      unused: null,
      status: "CONNECT_TO_CHECK",
    }));
  async function resolve(id: string, status: string) {
    try {
      await api(`/preparation/duplicates/${id}/resolve`, "POST", {
        status,
        notes: notes[id] || "",
      });
      await refresh();
      toast.success("Comparison decision saved");
    } catch (e: any) {
      toast.error(e.message);
    }
  }
  return (
    <div className="prep-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">CEN 02/2025 · GRADE-I SIGNAL</p>
          <h1>Exam Preparation</h1>
          <p>Source evidence, syllabus coverage and unused question stock.</p>
        </div>
      </div>
      <div className="notice">
        The 190 starter questions remain Basic Practice. Original patterns are
        labelled separately from PYQs. A supplementary paper copy is not
        official question-level verification.
      </div>
      {error && <p role="alert">{error}</p>}
      <div className="prep-stats">
        {[
          ["Basic practice", "basic"],
          ["Verified PYQs", "verified"],
          ["PYQ-matched patterns", "patterns"],
          ["Supplementary ready", "supplementary"],
        ].map(([label, key]) => (
          <section className="panel" key={key}>
            <span>{label}</span>
            <h2>{data ? data.summary[key] : "—"}</h2>
          </section>
        ))}
      </div>
      {!data && (
        <p className="muted">
          Connect your updated backend to inspect your database and previous
          attempts. The source register and official syllabus below can be read
          without a connection.
        </p>
      )}
      <section className="panel prep-section">
        <h2>Choose your practice</h2>
        <p>
          The mixed exam configuration still requires sufficient verified PYQs.
          Generated patterns require a verified actual PYQ, a source-alignment
          check and human approval. The 20 original challenges remain in
          Question Bank, but do not count as PYQ-matched coverage. Supplementary
          examples are independently solved but not matched to an official
          answer key.
        </p>
        <div className="prep-actions">
          <button
            className="btn primary"
            onClick={() => onStart("hard-patterns")}
          >
            Verified-foundation hard patterns · 10 questions
          </button>
          <button
            className="btn secondary"
            onClick={() => onStart("supplementary")}
          >
            Supplementary · 1 ready example
          </button>
          <button className="btn secondary" onClick={() => onStart("quick")}>
            Basic Practice
          </button>
        </div>
        <p className="muted">
          Hard-pattern and supplementary sessions exclude question IDs and
          numerical families already reserved in your saved history, including
          unfinished sessions. They stop on shortages. Similarity flags require
          human review; paraphrase detection is heuristic.
        </p>
      </section>
      <section className="panel prep-section">
        <h2>Material obtained</h2>
        <p>
          200 numbered records were extracted for inspection from two external
          PDFs. Only two short examples are imported; the linked full papers
          remain external references. At least 13 stems extracted incompletely,
          and other diagram/options or colour-coded keys can also need visual
          review. Officially authenticated question records obtained in this
          source collection: 0.
        </p>
        <div className="prep-table">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Status</th>
                <th>Records</th>
                <th>Evidence / limits</th>
              </tr>
            </thead>
            <tbody>
              {catalog.sources.map((s) => (
                <tr key={s.id}>
                  <td>
                    <a href={s.url} target="_blank" rel="noreferrer">
                      {s.title}
                    </a>
                  </td>
                  <td>{s.status.replaceAll("_", " ")}</td>
                  <td>{s.question_count}</td>
                  <td>{s.obtained}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel prep-section">
        <h2>Official syllabus coverage</h2>
        <p>
          {catalog.authority}. 100 questions · 90 minutes · −⅓ per wrong answer.
          Indicative allocation: Science & Engineering 35, Computers 20,
          Mathematics 20, Reasoning 15, General Awareness 10.
        </p>
        <p>{catalog.scope_note}</p>
        <p>
          <b>
            {data
              ? `${data.summary.missing_units} missing · ${data.summary.underrepresented_units} underrepresented`
              : "Coverage counts require your backend"}
          </b>{" "}
          · 75 checklist units. Supplementary stock is shown separately and does
          not satisfy the exam-bank target.
        </p>
        <Select value={subject} onValueChange={setSubject}>
          <SelectTrigger aria-label="Filter syllabus subject">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {["ALL", ...Object.keys(catalog.pattern.distribution)].map((s) => (
              <SelectItem key={s} value={s}>
                {s === "ALL" ? "All subjects" : s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="prep-table">
          <table>
            <thead>
              <tr>
                <th>Subject / syllabus unit</th>
                <th>Verified</th>
                <th>Patterns</th>
                <th>Supplementary</th>
                <th>Unused*</th>
                <th>Stock status</th>
              </tr>
            </thead>
            <tbody>
              {units
                .filter((u: Any) => subject === "ALL" || u.subject === subject)
                .map((u: Any) => (
                  <tr key={u.id}>
                    <td>
                      <small>{u.subject}</small>
                      <br />
                      {u.name}
                    </td>
                    <td>{u.verified ?? "—"}</td>
                    <td>{u.patterns ?? "—"}</td>
                    <td>{u.supplementary ?? "—"}</td>
                    <td>{u.unused ?? "—"}</td>
                    <td>{u.status.replaceAll("_", " ")}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <p className="muted">
          *Unused includes eligible supplementary examples, which remain
          excluded from the verified-PYQ mix. A stock target is not proof that
          every subtopic or difficulty has been mastered.
        </p>
      </section>
      <section className="panel prep-section">
        <h2>Answer-key conflicts</h2>
        <p>
          One 2026 example is withheld: the supplementary PDF marking conflicts
          with its independently solved answer. Review it in Question Bank →
          Admin Review before activation.
        </p>
        {data?.key_conflicts.map((q: Any) => (
          <p key={q.id}>
            <b>{q.id}</b>: {q.note}
          </p>
        ))}
        <h2>Possible duplicate review</h2>
        <p>
          Exact copies and simple numerical variants are excluded from
          preparation. Possible paraphrases are withheld until compared by an
          administrator. Archiving a duplicate preserves existing attempt
          snapshots.
        </p>
        {data?.duplicate_flags.length === 0 ? (
          <p>
            No pending similarity flags. This does not guarantee that no
            semantic duplicates exist.
          </p>
        ) : (
          data?.duplicate_flags.map((q: Any) => (
            <div className="panel prep-section" key={q.id}>
              <b>
                {q.id} ↔ {q.against}
              </b>
              <p>{q.text}</p>
              <p>{q.kind}</p>
              {admin && (
                <>
                  <textarea
                    aria-label={`Comparison rationale for ${q.id}`}
                    placeholder="Compare both questions in Question Bank; explain your decision"
                    value={notes[q.id] || ""}
                    onChange={(e) =>
                      setNotes({ ...notes, [q.id]: e.target.value })
                    }
                  />
                  <div className="prep-actions">
                    <button
                      className="btn secondary"
                      onClick={() => resolve(q.id, "ACTIVE")}
                    >
                      Distinct — clear flag
                    </button>
                    <button
                      className="btn secondary"
                      onClick={() => resolve(q.id, "ARCHIVED")}
                    >
                      Duplicate — archive
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </section>
    </div>
  );
}
