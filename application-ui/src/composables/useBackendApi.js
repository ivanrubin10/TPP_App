import axios from 'axios'
import { ref } from 'vue'
export function useBackendApi() {
  const baseUrl = 'http://127.0.0.1:5000'

  const capturedImage = ref('')
  const detectedObjects = ref([])
  const resultImage = ref('')
  const captureImage = async () => {
    try {
      const response = await axios.get(`${baseUrl}/capture-image`)
      const data = response.data
      console.log('Captured image:', data)
      capturedImage.value = `data:image/jpeg;base64,${data.image}`
      detectedObjects.value = data.objects
      resultImage.value = `data:image/jpeg;base64,${data.result_image}`
      return {
        image: `data:image/jpeg;base64,${data.image}`,
        objects: data.objects,
        resultImage: `data:image/jpeg;base64,${data.result_image}`
      }
    } catch (error) {
      console.error('Error capturing image:', error)
      throw error // Re-throw for handling in component
    }
  }

  return { captureImage, capturedImage, detectedObjects, resultImage }
}
