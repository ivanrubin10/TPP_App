import { defineStore } from 'pinia';
import { ref, computed, watchEffect } from 'vue';
import type { CarItem, AppConfig } from '@/types';
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json'
  }
});

export const useAppStore = defineStore('app', () => {
  // State
  const items = ref<CarItem[]>([]);
  const selectedItem = ref<CarItem | null>(null);
  const config = ref<AppConfig | null>(null);
  const isConnected = ref(false);
  const connectionType = ref<'PLC' | 'GALC'>('PLC');
  const isRetrying = ref(false);
  const isLoading = ref(false);

  // Computed
  const goodCount = computed(() => items.value.filter(item => item.outcome === 'GOOD').length);
  const noGoodCount = computed(() => items.value.filter(item => item.outcome === 'NOGOOD').length);
  const successRate = computed(() => {
    const total = items.value.length;
    return total > 0 ? Math.round((goodCount.value / total) * 100) : 0;
  });

  // API Functions
  async function fetchLogs(): Promise<CarItem[]> {
    try {
      const { data } = await api.get<any[]>('/logs');
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

  // Actions
  async function loadLogs(force = false) {
    if (isLoading.value && !force) return;

    isLoading.value = true;
    try {
      // First try to fetch logs
      let logs: CarItem[] = [];
      try {
        logs = await fetchLogs();
        console.log('Fetched logs:', logs);
      } catch (error) {
        console.error('Error fetching logs:', error);
      }

      // Then try to fetch queued cars
      let queuedCars: CarItem[] = [];
      try {
        queuedCars = await fetchQueuedCars();
        console.log('Fetched queued cars:', queuedCars);
      } catch (error) {
        console.error('Error fetching queued cars:', error);
      }

      // Update items with both logs and queued cars
      items.value = [...queuedCars, ...logs];
      console.log('Total items:', items.value.length);
    } catch (error) {
      console.error('Error in loadLogs:', error);
      items.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  // Load initial data
  loadLogs();
  loadConfig();

  async function retryConnection() {
    try {
      const { data } = await api.post('/retry-connection');
      return data;
    } catch (error) {
      console.error('Error retrying connection:', error);
      throw error;
    }
  }

  async function loadConfig() {
    try {
      const { data } = await api.get('/config');
      config.value = data;
      connectionType.value = data.connection_type;
    } catch (error) {
      console.error('Error loading config:', error);
    }
  }

  async function updateConfig(newConfig: Partial<AppConfig>) {
    try {
      if (!config.value) return;
      const defaultConfig: AppConfig = {
        min_conf_threshold: 0.7,
        connection_type: 'PLC',
        plc_host: '127.0.0.1',
        plc_port: 12345,
        galc_host: '127.0.0.1',
        galc_port: 54321
      };
      const { data } = await api.post('/config', {
        ...defaultConfig,
        ...config.value,
        ...newConfig
      });
      await loadConfig();
    } catch (error) {
      console.error('Error updating config:', error);
    }
  }

  function setSelectedItem(item: CarItem | null) {
    selectedItem.value = item;
  }

  function addItem(item: CarItem) {
    items.value = [item, ...items.value];
  }

  function updateItem(updatedItem: CarItem) {
    const index = items.value.findIndex(item => item.id === updatedItem.id);
    if (index !== -1) {
      const newItems = [...items.value];
      newItems[index] = updatedItem;
      items.value = newItems;
    }
  }

  function setConnectionStatus(status: boolean) {
    isConnected.value = status;
  }

  function setConnectionType(type: 'PLC' | 'GALC') {
    connectionType.value = type;
  }

  function setRetrying(status: boolean) {
    isRetrying.value = status;
  }

  return {
    // State
    items,
    selectedItem,
    config,
    isConnected,
    connectionType,
    isRetrying,
    isLoading,
    
    // Computed
    goodCount,
    noGoodCount,
    successRate,
    
    // Actions
    loadLogs,
    retryConnection,
    loadConfig,
    updateConfig,
    setSelectedItem,
    addItem,
    updateItem,
    setConnectionStatus,
    setConnectionType,
    setRetrying
  };
}); 