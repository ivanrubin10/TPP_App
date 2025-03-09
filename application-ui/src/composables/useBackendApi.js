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
      let url = `${baseUrl}/capture-image`
      
      // Add car parameters for ICS integration if provided
      if (carParams && carParams.car_id) {
        console.log('Adding car parameters to capture request:', carParams);
        url += `?car_id=${encodeURIComponent(carParams.car_id)}&expected_part=${encodeURIComponent(carParams.expected_part)}&actual_part=${encodeURIComponent(carParams.actual_part || '')}`
      }
      
      console.log('Sending capture request to:', url);
      const response = await axios.get(url)
      const data = response.data
      
      if (data.error) {
        console.warn('Capture endpoint returned error:', data.error);
      }
      
      capturedImage.value = `data:image/jpeg;base64,${data.image}`
      detectedObjects.value = data.objects || []
      resultImage.value = `data:image/jpeg;base64,${data.result_image}`
      
      return {
        image: `data:image/jpeg;base64,${data.image}`,
        objects: data.objects || [],
        resultImage: `data:image/jpeg;base64,${data.result_image}`,
        gray_percentage: data.gray_percentage,
        error: data.error,
        processing_time: data.processing_time,
        skip_database_update: data.skip_database_update,
        is_capo_tipo_1: data.is_capo_tipo_1
      }
    } catch (error) {
      console.error('Error capturing image:', error);
      if (error.response) {
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
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
      const response = await axios.put(`${baseUrl}/update-item`, item)
      return response.data
    } catch (error) {
      console.error('Error updating item:', error)
      throw error
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
