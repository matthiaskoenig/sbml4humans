import type { AnnotationInfo, ExampleMetaData, ReportResponse } from "@/api/types";

const API_URL: string = import.meta.env.VITE_API_URL;

/** A failure reported by the backend or a failure to reach it. */
export class ApiError extends Error {
  readonly traceback: string | null;
  readonly warnings: string[];

  constructor(message: string, traceback: string | null = null, warnings: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.traceback = traceback;
    this.warnings = warnings;
  }
}

/** Wrap an unknown thrown value into an ApiError. */
export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error;
  if (error instanceof Error) return new ApiError(error.message, error.stack ?? null);
  return new ApiError(String(error));
}

interface ErrorBody {
  errors: string[];
  warnings: string[];
  info: Record<string, string>;
}

/** The error contract: status 200 with a non-empty errors list and the info of the request. */
function isErrorBody(body: unknown): body is ErrorBody {
  if (typeof body !== "object" || body === null) return false;
  const candidate = body as Partial<ErrorBody>;
  return (
    Array.isArray(candidate.errors) &&
    candidate.errors.length > 0 &&
    typeof candidate.info === "object" &&
    candidate.info !== null
  );
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${path}`;
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    throw new ApiError(
      `The backend at ${API_URL} is not reachable`,
      error instanceof Error ? error.message : null,
    );
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError(`The backend answered with status ${response.status} and no JSON body`);
  }
  if (isErrorBody(body)) {
    throw new ApiError(body.errors[0] ?? "Unknown error", body.errors[1] ?? null, body.warnings);
  }
  if (!response.ok) {
    throw new ApiError(`The backend answered with status ${response.status}`);
  }
  return body as T;
}

/** Fetch the metadata of the examples the backend ships. */
export async function getExamples(): Promise<ExampleMetaData[]> {
  const body = await request<{ examples: ExampleMetaData[] }>("/examples");
  return body.examples;
}

/** Fetch the report of one example by its id. */
export function getExample(id: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/examples/${encodeURIComponent(id)}`);
}

/** Download and report the SBML (or COMBINE archive) at a url. */
export function getUrl(url: string): Promise<ReportResponse> {
  return request<ReportResponse>(`/url?url=${encodeURIComponent(url)}`);
}

/** Upload a file for its report, as the multipart field the backend expects. */
export function postFile(file: File): Promise<ReportResponse> {
  const form = new FormData();
  form.append("source", file, file.name);
  return request<ReportResponse>("/file", { method: "POST", body: form });
}

/** Report raw SBML content posted as the request body. */
export function postContent(text: string): Promise<ReportResponse> {
  return request<ReportResponse>("/content", {
    method: "POST",
    body: text,
    headers: { "Content-Type": "application/xml" },
  });
}

/** Resolve an annotation resource (identifiers.org and similar) via pymetadata. */
export function getAnnotationResource(resource: string): Promise<AnnotationInfo> {
  return request<AnnotationInfo>(`/annotation_resource?resource=${encodeURIComponent(resource)}`);
}
