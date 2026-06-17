import { Question } from "@/lib/api";

// Add this interface for the grade object structure
export interface FileGrade {
  grade_percentage: number;
  detected_nature_code?: string;
  nature_code_name?: string;
  nature_code_reasoning?: string;
  grades?: {
    [questionId: string]: {
      code: string;
      label: string;
      status: string;
      reasoning?: string;
    };
  };
  per_question?: {
    [questionId: string]: {
      code: string;
      label: string;
      status: string;
      reasoning?: string;
    };
  };
}

export interface FileParts {
  name: string;
  dateTime: Date;
  nature: string;
  description: string;
  extension: string;
}

export interface DispatcherRecord {
  name: string;
  audioFile?: string;
  cdrFile?: string;
  transcriptFile?: string;
  gradeFile?: string;
  otherFiles?: string[];
}

export interface Dispatcher {
  id: string;
  name: string;
  overallGrade?: number;
  numRecords?: number;
  numTranscripts?: number;
  numGrades?: number;
  files?: {
    transcriptFiles: string[]; // Transcripted Json Files
    audioFiles: string[]; // Audio Files to be Used when listening to the call
  };
  records?: DispatcherRecord[];
  grades?: {
    [filename: string]: FileGrade; // Changed from string | number to FileGrade
  };
  notAskedQuestions?: Question[];
  questionsAskedIncorrectly?: Question[];
}
