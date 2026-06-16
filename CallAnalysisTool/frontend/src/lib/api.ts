import type { DispatcherRecord, FileGrade } from "@/types/dispatcher";

const API_PORT = process.env.NEXT_PUBLIC_API_PORT || "5001";
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export function getApiBaseUrl(): string {
  if (API_URL) {
    return API_URL;
  }

  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:${API_PORT}`;
  }

  return `http://127.0.0.1:${API_PORT}`;
}

export interface ApiResponse {
  filename: string;
  grader_type: string;
  grade_percentage: number;
  detected_nature_code: string;
  nature_code_reasoning?: string;
  total_questions: number;
  case_entry_questions: number;
  nature_code_questions: number;
  questions_asked_correctly: number;
  questions_missed: number;
  timestamp: string;
  grades: {
    [questionId: string]: {
      code: string;
      label: string;
      status: string;
    };
  };
  metadata: {
    language: string;
    segment_count: number;
    grader_version: string;
    model: string;
    questions_source: string;
    nature_code_detection: string;
  };
}

export interface UploadPipelineResponse {
  outputDestination: string;
  dispatcherName: string;
  grades: ApiResponse;
}

export interface Question {
  questionId: string;
  label: string;
}

export interface NatureCodeOption {
  id: string;
  name: string;
}

export interface NatureCodeGradeTemplate {
  detected_nature_code: string;
  nature_code_name?: string;
  grades: {
    [questionId: string]: {
      code: string;
      label: string;
      status: string;
      reasoning?: string;
    };
  };
}

export interface RegradeResponse {
  outputDestination: string;
  dispatcherName: string;
  grades: ApiResponse;
  renamed_files?: Record<string, string>;
}

interface DispatcherSummaryResponse {
  stationGrade?: number | null;
  dispatchers?: Array<{
    name?: string;
    overallGrade?: number;
    numRecords?: number;
    numTranscripts?: number;
    numGrades?: number;
  }>;
}

interface DispatcherRecordsResponse {
  records?: string[];
}

export interface DispatcherDateRangeParams {
  startDate?: string;
  endDate?: string;
}

interface RecordDetailsResponse {
  audioFiles?: string[];
  cdrFiles?: string[];
  transcriptFiles?: string[];
  gradeFiles?: string[];
  otherFiles?: string[];
}

type DispatcherSummaryItem = NonNullable<
  DispatcherSummaryResponse["dispatchers"]
>[number];

/**
 * Upload a JSON file to the API and get analysis results
 */
export async function uploadFileForAnalysis(
  file: File
): Promise<UploadPipelineResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return postUploadRequest(formData);
}

export async function uploadTranscriptForAnalysis(
  transcriptData: unknown
): Promise<UploadPipelineResponse> {
  return postUploadRequest(JSON.stringify(transcriptData), {
    "Content-Type": "application/json",
  });
}

async function postUploadRequest(
  body: BodyInit,
  headers?: HeadersInit
): Promise<UploadPipelineResponse> {
  const apiBaseUrl = getApiBaseUrl();

  try {
    const response = await fetch(`${apiBaseUrl}/api/upload`, {
      method: "POST",
      headers,
      body,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new Error(
        `API error (${response.status}): ${errorText || response.statusText}`
      );
    }

    // Handle different response types
    const data = await response.json();

    // If the response is a string, try to parse it
    if (typeof data === "string") {
      try {
        return JSON.parse(data);
      } catch {
        throw new Error("Invalid response format from API");
      }
    }

    return data;
  } catch (error) {
    // Handle network errors specifically
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new Error(
        `Failed to connect to API at ${apiBaseUrl}. Make sure the backend server is running on port ${API_PORT}.`
      );
    }
    // Re-throw other errors
    throw error;
  }
}

/**
 * Calculate a grade from the API response
 * Simply returns the grade_percentage that the backend already calculated
 */
export function calculateGrade(response: ApiResponse): number {
  return Math.round(response.grade_percentage ?? 0);
}

/**
 * Get questions that were not asked from the API response
 * Returns an array of objects containing questionId and label for questions that were not asked
 */

export function getNotAskedQuestions(response: ApiResponse): Question[] {
  if (!response.grades) {
    return [];
  }

  // Convert grades object to array and filter for "Not Asked" questions
  return Object.entries(response.grades)
    .filter(
      ([, grade]) =>
        grade.status === "Not Asked" || grade.code === "2"
    )
    .map(([questionId, grade]) => ({
      questionId,
      label: grade.label,
    }));
}

//Get Questions that were asked incorrectly from the API response
export function getQuestionsAskedIncorrectly(
  response: ApiResponse
): Question[] {
  if (!response.grades) {
    return [];
  }

  return Object.entries(response.grades)
    .filter(
      ([, grade]) =>
        grade.status === "Asked Incorrectly" || grade.code === "3"
    )
    .map(([questionId, grade]) => ({
      questionId,
      label: grade.label,
    }));
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`);

  if (!response.ok) {
    throw new Error(`API error (${response.status}): ${response.statusText}`);
  }

  return response.json();
}

function formatDateForDispatcherQuery(dateValue?: string): string | undefined {
  if (!dateValue) {
    return undefined;
  }

  const [year, month, day] = dateValue.split("-");
  if (!year || !month || !day) {
    return undefined;
  }

  return `${year}${month}${day}`;
}

function buildDispatcherQuery(params?: DispatcherDateRangeParams): string {
  const searchParams = new URLSearchParams();
  const startDate = formatDateForDispatcherQuery(params?.startDate);
  const endDate = formatDateForDispatcherQuery(params?.endDate);

  if (startDate) {
    searchParams.set("start_date", startDate);
  }

  if (endDate) {
    searchParams.set("end_date", endDate);
  }

  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export async function fetchDispatchers(
  params?: DispatcherDateRangeParams
): Promise<DispatcherSummaryResponse> {
  return fetchJson<DispatcherSummaryResponse>(
    `/api/dispatchers${buildDispatcherQuery(params)}`
  );
}

export type { DispatcherSummaryItem, DispatcherSummaryResponse };

export async function fetchDispatcherRecords(
  dispatcherName: string,
  params?: DispatcherDateRangeParams
): Promise<string[]> {
  const response = await fetchJson<DispatcherRecordsResponse>(
    `/api/dispatchers/${encodeURIComponent(dispatcherName)}${buildDispatcherQuery(
      params
    )}`
  );

  return Array.isArray(response.records) ? response.records : [];
}

export async function fetchDispatcherRecordDetails(
  dispatcherName: string,
  recordName: string
): Promise<DispatcherRecord> {
  const response = await fetchJson<RecordDetailsResponse>(
    `/api/dispatchers/${encodeURIComponent(
      dispatcherName
    )}/${encodeURIComponent(recordName)}`
  );

  return {
    name: recordName,
    audioFile: response.audioFiles?.[0],
    cdrFile: response.cdrFiles?.[0],
    transcriptFile: response.transcriptFiles?.[0],
    gradeFile: response.gradeFiles?.[0],
    otherFiles: response.otherFiles || [],
  };
}

export async function fetchGradeFile(filename: string): Promise<FileGrade> {
  return fetchJson<FileGrade>(`/api/files/${encodeURIComponent(filename)}`);
}

export async function fetchBackendFile<T>(filename: string): Promise<T> {
  return fetchJson<T>(`/api/files/${encodeURIComponent(filename)}`);
}

export async function fetchNatureCodeOptions(): Promise<NatureCodeOption[]> {
  return fetchJson<NatureCodeOption[]>(`/api/files/nature-codes`);
}

export async function fetchNatureCodeGradeTemplate(
  natureCodeId: string
): Promise<NatureCodeGradeTemplate> {
  return fetchJson<NatureCodeGradeTemplate>(
    `/api/files/nature-codes/${encodeURIComponent(natureCodeId)}`
  );
}

export async function putBackendFile<TResponse = unknown>(
  filename: string,
  data: unknown
): Promise<TResponse> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/files/${encodeURIComponent(filename)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
  }

  return response.json();
}

export async function regradeRecord(
  dispatcherName: string,
  recordName: string
): Promise<RegradeResponse> {
  const response = await fetch(
    `${getApiBaseUrl()}/api/regrade/${encodeURIComponent(dispatcherName)}/${encodeURIComponent(recordName)}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
  }

  return response.json();
}

export function buildBackendFileUrl(filename: string): string {
  return `${getApiBaseUrl()}/api/files/${encodeURIComponent(filename)}`;
}
