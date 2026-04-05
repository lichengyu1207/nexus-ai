export interface ReasoningStep {
  step: string;
  content: string;
  timestamp: string;
  feedbackGiven?: boolean;
}

export interface FeedbackRequest {
  stepIndex: number;
  feedback: 'helpful' | 'not_helpful';
}

export interface FeedbackResponse {
  success: boolean;
}
