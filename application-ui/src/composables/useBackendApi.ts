import axios from 'axios';
import type { CarItem, AppConfig, ApiResponse } from '@/types';

const api = axios.create({
  baseURL: 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json'
  }
});

interface CaptureImageParams {
  car_id?: string;
  expected_part?: string;
  actual_part?: string;
}

interface CaptureImageResponse {
  image: string;
  objects: Array<{
    class: string;
    score: number;
    box: number[];
  }>;
  result_image: string;
}

export function useBackendApi() {
  async function fetchLogs(): Promise<CarItem[]> {
    try {
      const { data } = await api.get<any[]>('/logs');
      console.log('Raw logs data:', data);
      if (!Array.isArray(data)) {
        console.error('Unexpected response format from /logs:', data);
        return [];
      }
      return data.map(item => ({
        id: item.car_id || '',
        expectedPart: item.expected_part || '',
        actualPart: item.actual_part || '',
        outcome: item.outcome || '',
        image: item.original_image_path || '',
        resultImage: item.result_image_path || '',
        date: item.date || '',
        isQueued: false
      }));
    } catch (error) {
      console.error('Error fetching logs:', error);
      return [];
    }
  }

  async function fetchQueuedCars(): Promise<CarItem[]> {
    try {
      const { data } = await api.get<any[]>('/queued-cars');
      console.log('Raw queued cars data:', data);
      if (!Array.isArray(data)) {
        console.error('Unexpected response format from /queued-cars:', data);
        return [];
      }
      return data.map(car => ({
        id: car.car_id || '',
        expectedPart: car.expected_part || '',
        actualPart: '',
        outcome: '',
        image: '',
        resultImage: '',
        date: car.date || '',
        isQueued: true
      }));
    } catch (error) {
      console.error('Error fetching queued cars:', error);
      return [];
    }
  }

  async function captureImage(carParams?: CaptureImageParams): Promise<CaptureImageResponse> {
    try {
      let url = '/capture-image';
      if (carParams) {
        const params = new URLSearchParams({
          car_id: carParams.car_id || '',
          expected_part: carParams.expected_part || '',
          actual_part: carParams.actual_part || ''
        });
        url += `?${params.toString()}`;
      }
      
      const { data } = await api.get<CaptureImageResponse>(url);
      return {
        image: `data:image/jpeg;base64,${data.image}`,
        objects: data.objects,
        result_image: `data:image/jpeg;base64,${data.result_image}`
      };
    } catch (error) {
      console.error('Error capturing image:', error);
      throw error;
    }
  }

  async function checkCarExists(carId: string): Promise<{ exists: boolean; car_log?: CarItem }> {
    try {
      const { data } = await api.get(`/check-car/${carId}`);
      return data;
    } catch (error) {
      console.error('Error checking car existence:', error);
      throw error;
    }
  }

  async function updateItem(item: CarItem): Promise<CarItem> {
    try {
      const { data } = await api.put<CarItem>('/update-item', item);
      return data;
    } catch (error) {
      console.error('Error updating item:', error);
      throw error;
    }
  }

  async function addLog(log: Omit<CarItem, 'id'>): Promise<CarItem> {
    try {
      const { data } = await api.post<CarItem>('/log', log);
      return data;
    } catch (error) {
      console.error('Error adding log:', error);
      throw error;
    }
  }

  async function getConfig(): Promise<AppConfig> {
    try {
      const { data } = await api.get<AppConfig>('/config');
      return data;
    } catch (error) {
      console.error('Error fetching config:', error);
      throw error;
    }
  }

  async function saveConfig(config: AppConfig): Promise<ApiResponse<void>> {
    try {
      const { data } = await api.post<ApiResponse<void>>('/config', config);
      return data;
    } catch (error) {
      console.error('Error saving config:', error);
      throw error;
    }
  }

  async function retryConnection(): Promise<ApiResponse<void>> {
    try {
      const { data } = await api.post<ApiResponse<void>>('/retry-connection');
      return data;
    } catch (error) {
      console.error('Error retrying connection:', error);
      throw error;
    }
  }

  async function sendToICS(data: {
    car_id: string;
    expected_part: string;
    actual_part: string;
    image: string;
  }): Promise<ApiResponse<void>> {
    try {
      const { data: response } = await api.post<ApiResponse<void>>('/send-to-ics', data);
      return response;
    } catch (error) {
      console.error('Error sending to ICS:', error);
      throw error;
    }
  }

  return {
    fetchLogs,
    fetchQueuedCars,
    captureImage,
    checkCarExists,
    updateItem,
    addLog,
    getConfig,
    saveConfig,
    retryConnection,
    sendToICS
  };
} 