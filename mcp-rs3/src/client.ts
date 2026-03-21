/**
 * Client HTTP RS3 — auth Bearer, gestion erreurs.
 */

const API_URL =
  process.env.RS3_API_URL ?? "https://rs3-api-production.up.railway.app";
const API_KEY = process.env.RS3_API_KEY ?? "";

if (!API_KEY) {
  process.stderr.write(
    "⚠️  RS3_API_KEY non défini — les endpoints authentifiés échoueront\n"
  );
}

export async function rs3Request<T = unknown>(
  method: string,
  path: string,
  body?: unknown
): Promise<T> {
  const url = `${API_URL}${path}`;
  const headers: Record<string, string> = {
    Authorization: `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  };

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText);
    throw new Error(`RS3 ${method} ${path} → ${res.status}: ${err}`);
  }

  return res.json() as Promise<T>;
}

export const rs3 = {
  get: <T = unknown>(path: string) => rs3Request<T>("GET", path),
  post: <T = unknown>(path: string, body?: unknown) =>
    rs3Request<T>("POST", path, body),
  put: <T = unknown>(path: string, body?: unknown) =>
    rs3Request<T>("PUT", path, body),
  del: <T = unknown>(path: string) => rs3Request<T>("DELETE", path),
};
