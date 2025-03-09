import { Ref } from 'vue'

interface BackendApi {
  captureImage: (carParams?: { car_id: string; expected_part: string; actual_part: string }) => Promise<{
    image: string;
    objects: any[];
    resultImage: string;
    error?: string;
    gray_percentage?: number;
    processing_time?: number;
    skip_database_update?: boolean;
  }>;
  capturedImage: Ref<string>;
  detectedObjects: Ref<any[]>;
  resultImage: Ref<string>;
  logs: Ref<any[]>;
  fetchLogs: () => Promise<any[]>;
  checkCarExists: (carId: string) => Promise<{ exists: boolean; car_log?: any }>;
  updateItem: (item: any) => Promise<any>;
  addLog: (log: any) => Promise<any>;
  getConfig: () => Promise<any>;
  saveConfig: (config: any) => Promise<any>;
  retryConnection: () => Promise<any>;
  sendToICS: (data: any) => Promise<any>;
}

export function useBackendApi(): BackendApi; 