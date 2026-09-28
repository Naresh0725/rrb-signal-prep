export type Question = {
  id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_option?: string;
  explanation?: string;
  concept?: string;
  formula?: string;
  given?: string;
  calculation?: string;
  final_answer?: string;
  why_correct?: string;
  why_wrong?: Record<string, string> | null;
  subject: string;
  topic: string;
  subtopic: string;
  difficulty: string;
  source_type: string;
  source_reference: string;
  status: string;
  exam_year?: number | null;
  parent_question_id?: string | null;
  generation_metadata?: Record<string, unknown> & { syllabus_units?: string[] };
  bookmarked?: boolean;
  [key: string]: unknown;
};
export const subjects = [
  "Science & Engineering",
  "Computers",
  "Mathematics",
  "Reasoning",
  "General Awareness",
];
export let base = "/api/backend";
let token = "";
export function configure(url: string) {
  base = url ? url.replace(/\/$/, "") + "/api" : "/api/backend";
  localStorage.setItem("signalprep-api", url);
  token = "";
}
export function setToken(value: string) {
  token = value;
}
export async function api(
  path: string,
  method = "GET",
  data?: unknown,
): Promise<any> {
  const r = await fetch(base + path, {
    method,
    headers: {
      ...(data instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    ...(data !== undefined
      ? { body: data instanceof FormData ? data : JSON.stringify(data) }
      : {}),
  });
  let b: any;
  try {
    b = await r.json();
  } catch {
    throw Error("The API returned an invalid response");
  }
  if (!r.ok)
    throw Error(
      typeof b.detail === "string" ? b.detail : JSON.stringify(b.detail || b),
    );
  return b;
}
