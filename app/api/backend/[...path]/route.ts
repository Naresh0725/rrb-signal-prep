import { env } from "cloudflare:workers";
export const dynamic = "force-dynamic";
async function proxy(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const runtime = env as unknown as Record<string, string>;
  const base = runtime.BACKEND_URL || process.env.BACKEND_URL;
  if (!base)
    return Response.json(
      {
        detail:
          "Backend is not connected. Use Settings to connect your deployed API.",
      },
      { status: 503 },
    );
  const { path } = await params;
  if (path.some((p) => p === ".." || p.includes("/")))
    return new Response("Invalid path", { status: 400 });
  const headers = new Headers();
  for (const key of ["authorization", "content-type"])
    if (request.headers.has(key)) headers.set(key, request.headers.get(key)!);
  try {
    const r = await fetch(
      base.replace(/\/$/, "") +
        "/api/" +
        path.map(encodeURIComponent).join("/") +
        new URL(request.url).search,
      {
        method: request.method,
        headers,
        body: ["GET", "HEAD"].includes(request.method)
          ? undefined
          : await request.arrayBuffer(),
        redirect: "error",
      },
    );
    return new Response(r.body, {
      status: r.status,
      headers: {
        "Content-Type": r.headers.get("Content-Type") || "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      { detail: "Backend is unavailable. Please try again." },
      { status: 502 },
    );
  }
}
export { proxy as GET, proxy as POST, proxy as PUT, proxy as DELETE };
