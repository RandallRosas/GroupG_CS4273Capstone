import { Question } from "@/lib/api";

// Add this interface for the grade object structure
export interface FileGrade {
  grade_percentage: number;
  detected_nature_code?: string;
  per_question?: {
    [questionId: string]: {
      code: string;
      label: string;
      status: string;
    };
  };
}

export interface Dispatcher {
  id: string;
  name: string;
  files: {
    transcriptFiles: string[]; // Transcripted Json Files
    audioFiles: string[]; // Audio Files to be Used when listening to the call
  };
  grades?: {
    [filename: string]: FileGrade; // Changed from string | number to FileGrade
  };
  notAskedQuestions?: Question[];
  questionsAskedIncorrectly?: Question[];
}
