import axios from 'axios'
import { ref } from 'vue'

export function useBackendApi() {
  const baseUrl = 'http://localhost:5000'

  const capturedImage = ref('')
  const detectedObjects = ref([])
  const resultImage = ref('')
  const logs = ref([])

   const captureImage = async (carParams) => {
    try {
      let url = `${baseUrl}/capture-image`;
      
      // Add compression flag to request
      const requestData = {
        ...(carParams || {}),
        compress_images: true,
        _t: Date.now()
      };
      
      console.log('Sending capture request...');
      const startTime = performance.now();
      
      // Use AbortController with shorter timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);
      
      const response = await axios({
        method: 'POST',
        url,
        data: requestData,
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        timeout: 15000
      });
      
      clearTimeout(timeoutId);
      
      const endTime = performance.now();
      console.log(`Capture request completed in ${(endTime - startTime).toFixed(2)}ms`);
      
      const responseData = response.data;
      
      if (responseData.error || responseData.warning) {
        console.warn(responseData.error || responseData.warning);
      }
      
      // Update refs with base64 images directly
      if (responseData.image) capturedImage.value = `data:image/jpeg;base64,${responseData.image}`;
      if (responseData.result_image) resultImage.value = `data:image/jpeg;base64,${responseData.result_image}`;
      if (responseData.objects?.length) detectedObjects.value = responseData.objects;
      
      return {
        image: responseData.image ? `data:image/jpeg;base64,${responseData.image}` : null,
        objects: responseData.objects || [],
        resultImage: responseData.result_image ? `data:image/jpeg;base64,${responseData.result_image}` : null,
        gray_percentage: responseData.gray_percentage,
        error: responseData.error,
        processing_time: responseData.processing_time,
        skip_database_update: responseData.skip_database_update,
        is_capo_tipo_1: responseData.is_capo_tipo_1,
        using_placeholder: responseData.using_placeholder,
        warning: responseData.warning,
        hood_detected: responseData.objects?.some(obj => obj.class.toLowerCase().includes('capo') || obj.class.toLowerCase().includes('hood'))
      };
    } catch (error) {
      console.error('Error capturing image:', error);
      if (error.name === 'AbortError') {
        throw new Error('La solicitud tardó demasiado tiempo en completarse');
      }
      if (error.response) {
        console.error('Error response:', error.response.status, error.response.data);
        throw new Error(`Error del servidor: ${error.response.status}`);
      }
      throw error;
    }
  }

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${baseUrl}/logs`)
      logs.value = response.data
      return logs.value
    } catch (error) {
      console.error('Error fetching logs:', error)
      throw error
    }
  }

  const checkCarExists = async (carId) => {
    try {
      const response = await axios.get(`${baseUrl}/check-car/${carId}`)
      return response.data
    } catch (error) {
      console.error('Error checking car existence:', error)
      throw error
    }
  }

  const updateItem = async (item) => {
    try {
      console.log('Starting update item request with data:', {
        ...item,
        original_image: item.original_image ? '[IMAGE DATA]' : null,
        result_image: item.result_image ? '[IMAGE DATA]' : null
      });
      const startTime = performance.now();
      
      // Set a longer timeout for large image updates
      const timeout = item.skip_image_update ? 10000 : 30000;
      
      // Ensure all required fields are present
      if (!item.car_id) {
        throw new Error('Missing car_id in update data');
      }
      
      const response = await axios.put(`${baseUrl}/update-item`, item, {
        timeout: timeout,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      
      const endTime = performance.now();
      console.log(`Update item request completed in ${(endTime - startTime).toFixed(2)}ms`);
      
      return response.data;
    } catch (error) {
      console.error('Error updating item:', error);
      if (error.response) {
        console.error('Server response:', error.response.status, error.response.data);
      }
      if (error.code === 'ECONNABORTED') {
        throw new Error('La solicitud tardó demasiado tiempo en completarse');
      }
      if (error.response?.status === 404) {
        throw new Error('No se encontró el coche en la base de datos');
      }
      throw error;
    }
  }

  const addLog = async (log) => {
    try {
      const response = await axios.post(`${baseUrl}/log`, log)
      return response.data
    } catch (error) {
      console.error('Error adding log:', error)
      throw error
    }
  }

  const getConfig = async () => {
    try {
      const response = await axios.get(`${baseUrl}/config`)
      return response.data
    } catch (error) {
      console.error('Error fetching config:', error)
      throw error
    }
  }
  const saveConfig = async (config) => {
    try {
      const response = await axios.post(`${baseUrl}/config`, config)
      return response.data
    } catch (error) {
      console.error('Error saving config:', error)
      throw error
    }
  }

  const retryConnection = async () => {
    try {
      const response = await axios.post(`${baseUrl}/retry-connection`)
      return response.data
    } catch (error) {
      console.error('Error retrying connection:', error)
      throw error
    }
  }

  const sendToICS = async (data) => {
    try {
      const response = await axios.post(`${baseUrl}/send-to-ics`, data)
      return response.data
    } catch (error) {
      console.error('Error sending to ICS:', error)
      throw error
    }
  }

  return {
    captureImage,
    capturedImage,
    detectedObjects,
    resultImage,
    fetchLogs,
    logs,
    checkCarExists,
    updateItem,
    addLog,
    getConfig,
    saveConfig,
    retryConnection,
    sendToICS,
  }
}
