export interface BackendApi {
  captureImage: (carParams: any) => Promise<any>;
  capturedImage: any;
  detectedObjects: any[];
  resultImage: any;
  fetchLogs: () => Promise<any[]>;
  logs: any[];
  checkCarExists: (carId: string) => Promise<any>;
  updateItem: (item: any) => Promise<any>;
  addLog: (log: any) => Promise<any>;
  getConfig: () => Promise<any>;
  saveConfig: (config: any) => Promise<any>;
  retryConnection: () => Promise<any>;
  sendToICS: (data: any) => Promise<any>;
  addFeedback: (feedbackData: any) => Promise<any>;
  getFeedbackLogs: (filters?: any) => Promise<any[]>;
  checkFeedbackExists: (carId: string) => Promise<any>;
}

export function useBackendApi(): BackendApi; 