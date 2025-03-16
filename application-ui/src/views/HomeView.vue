<template>
  <div class="content">
    <div class="connection-status" @click="handleRetryConnection">
      <div class="status-circle" :class="{ 'connected': isConnected }"></div>
      <span>{{ isConnected ? `${connectionType} Conectado` : `${connectionType} Desconectado` }}</span>
      <svg class="reload-icon" :class="{ 'spinning': isRetrying }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </div>
    
    <div class="container" v-if="selectedItem">
      <div class="inspection-header">
        <p>{{ selectedItem.id }}</p>
        <p>{{ selectedItem.date }}</p>
      </div>
      <InspectionResults v-model="selectedItem" />
      <div class="inspection-footer">
        <div v-if="isLoading" class="loading-indicator">
          <svg class="spinning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>{{ loadingMessage }}</span>
        </div>
        <template v-else>
          <FalseOutcomeButton v-if="!selectedItem.resultImage" @click="handleClick" text="Detectar" />
          <FalseOutcomeButton v-else @click="handleClick" text="Detectar nuevamente" />
          <FalseOutcomeButton v-show="selectedItem.outcome === 'NOGOOD'" @click="noEsDefecto(selectedItem)"
            text="No es defecto" />
          <FalseOutcomeButton v-show="selectedItem.outcome === 'GOOD'" @click="esDefecto(selectedItem)"
            text="Es defecto" />
        </template>
      </div>
    </div>
    <div class="container" v-else>
      <div class="no-item-selected">
        Por favor seleccione un coche de la lista para ver su estado
      </div>
    </div>
    <CarsFooter 
      :items="items" 
      @item-clicked="handleItemClicked" 
      :modelValue="selectedItem || undefined" 
      @update:modelValue="val => selectedItem = val" 
    />
    <div v-if="errorMessage" class="error-message-container">
      <div class="error-message">{{ errorMessage }}</div>
    </div>
  </div>
</template>


<script lang="ts" setup>
import { useBackendApi } from '../composables/useBackendApi'
import CarsFooter from '../components/CarsFooter.vue'
import FalseOutcomeButton from '../components/FalseOutcomeButton.vue'
import InspectionResults from '../components/InspectionResults.vue'
import { onBeforeUnmount, onMounted, ref, onUnmounted, nextTick } from 'vue';
import socket from '../composables/socket';
import axios from 'axios';

const baseUrl = 'http://localhost:5000'

interface Item {
  id: string;
  expectedPart: string;
  actualPart: string;
  outcome: string;
  image: string;
  resultImage: string;
  date: string;
  grayPercentage?: number;
  isQueued: boolean;
  isProcessing: boolean;
}

interface CaptureResponse {
  image: string;
  objects: any[];
  resultImage: string;
  gray_percentage?: number;
  error?: string;
  processing_time?: number;
  skip_database_update?: boolean;
  is_capo_tipo_1?: boolean;
  using_placeholder?: boolean;
  warning?: string;
  hood_detected?: boolean;
}

interface LogResponse {
  car_id: string;
  expected_part: string;
  actual_part: string;
  outcome: string;
  original_image: string;
  result_image: string;
  date: string;
}

const items = ref<Item[]>([]);
const selectedItem = ref<Item | null>(null);
const isConnected = ref(false);
const connectionType = ref('PLC');
const messageBeingHandled = ref(false);
const isProcessing = ref(false);

const isRetrying = ref(false);
const isLoading = ref(false);
const loadingMessage = ref('');
const errorMessage = ref('');
const activeDetectionCarId = ref<string | null>(null);

const { 
  captureImage,
  detectedObjects,
  fetchLogs,
  checkCarExists,
  updateItem,
  addLog,
  retryConnection,
  sendToICS,
  getConfig,
  saveConfig } = useBackendApi()

let clickHandle = false;

const fetchQueuedCars = async () => {
  try {
    const response = await axios.get(`${baseUrl}/queued-cars`)
    return response.data
  } catch (error) {
    console.error('Error fetching queued cars:', error)
    throw error
  }
}

const processQueuedCar = async (carId: string) => {
  try {
    const response = await axios.post(`${baseUrl}/process-queued-car/${carId}`)
    return response.data
  } catch (error) {
    console.error('Error processing queued car:', error)
    throw error
  }
}

// Add a sorting function
const sortItems = (items: Item[]) => {
  return items.sort((a, b) => {
    // First, prioritize queued (undetected) cars
    if (a.isQueued && !b.isQueued) return -1;
    if (!a.isQueued && b.isQueued) return 1;
    
    // Then sort by date (newest first)
    const dateA = new Date(a.date.split(' ')[0].split('-').reverse().join('-'));
    const dateB = new Date(b.date.split(' ')[0].split('-').reverse().join('-'));
    return dateB.getTime() - dateA.getTime();
  });
};

// Function to manually trigger detection for a car
const triggerManualDetection = async (carId: string) => {
  console.log(`Manually triggering detection for car ${carId}`);
  
  // Double-check that the car exists in our items list
  const carIndex = items.value.findIndex(item => item.id === carId);
  if (carIndex === -1) {
    console.error(`Cannot trigger detection - car ${carId} not found in items list`);
    return;
  }
  
  // Get a direct reference to the item in the array
  const carItem = items.value[carIndex];
  console.log('Car item being selected for detection:', carItem);
  
  // Ensure the correct car is selected
  selectedItem.value = carItem;
  
  // Wait for Vue to update the DOM with the selection
  nextTick(async () => {
    console.log('DOM updated after selection, starting detection');
    
    try {
      // Verify selectedItem is correct before proceeding
      if (!selectedItem.value || selectedItem.value.id !== carId) {
        console.error('Selected item changed before detection could start');
        selectedItem.value = carItem; // Try to reset it
        
        // Wait one more tick to be absolutely sure
        await nextTick();
        if (!selectedItem.value || selectedItem.value.id !== carId) {
          throw new Error('Cannot maintain car selection for detection');
        }
      }
      
      // Now trigger detection
      await detectObjects();
    } catch (error) {
      console.error('Error during car selection or detection:', error);
      errorMessage.value = `Error al iniciar detección: ${error instanceof Error ? error.message : 'Error desconocido'}`;
      setTimeout(() => errorMessage.value = '', 5000);
      
      // Reset loading state
      isLoading.value = false;
      loadingMessage.value = '';
      activeDetectionCarId.value = null;
    }
  });
};

onMounted(async () => {
  // Get initial config to set connection type
  await loadConfig();
  const config = await getConfig();
  connectionType.value = config.connection_type;

  socket.on('connection_status', (data: any) => {
    isConnected.value = data.status;
  });

  socket.on('connection_type', (data: any) => {
    connectionType.value = data.type;
  });
  
  socket.on('plc_message', async (data: any) => {
    console.log('Received PLC message:', data);
  });

  socket.on('handle_message', async (data: any) => {
    if (!messageBeingHandled.value) {
      messageBeingHandled.value = true;
      try {
        await handleMessage(data);
      } finally {
        messageBeingHandled.value = false;
      }
    }
  });

  async function handleMessage(data: any) {
    try {
      const currentDate = new Date();
      const formattedDate = `${String(currentDate.getDate()).padStart(2, '0')}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${currentDate.getFullYear()} ${String(currentDate.getHours()).padStart(2, '0')}:${String(currentDate.getMinutes()).padStart(2, '0')}:${String(currentDate.getSeconds()).padStart(2, '0')}`;
      
      let expectedPart = '';
      switch(data.message) {
        case '01':
          expectedPart = 'Capo tipo 1';
          break;
        case '05':
          expectedPart = 'Capo tipo 2'; 
          break;
        case '08':
          expectedPart = 'Capo tipo 3';
          break;
        default:
          console.warn('Unknown message type:', data.message);
          return;
      }

      // This function now only handles GALC messages
      // GALC messages are queued and don't need immediate processing
      console.log('GALC message processed');
    } catch (error) {
      console.error('Error handling message:', error);
    }
  }

  // Listen for new cars from PLC
  socket.on('new_car', (car: any) => {
    console.log('Received new car from PLC:', car);
    
    // Check if the car already exists in our list
    const existingCarIndex = items.value.findIndex(item => item.id === car.car_id);
    if (existingCarIndex !== -1) {
        console.log('Car already exists in list, skipping creation');
        return;
    }
    
    // Add the new car to the items list
    const newCar: Item = {
        id: car.car_id,
        expectedPart: car.expected_part,
        actualPart: "Pendiente",
        outcome: "Pendiente",
        image: '',
        resultImage: '',
        date: car.date,
        isQueued: false,
        isProcessing: true
    };

    // Add the car to the list and sort
    items.value.push(newCar);
    items.value = sortItems(items.value);

    // Set as selected item
    selectedItem.value = newCar;
    
    // Show loading indicator
    isLoading.value = true;
    loadingMessage.value = 'Procesando detección...';
  });

  // Listen for detection completion
  socket.on('detection_complete', (result: any) => {
    console.log('Detection completed:', result);
    
    // Find the car in our list
    const carIndex = items.value.findIndex(item => item.id === result.car_id);
    if (carIndex !== -1) {
      // Update the car with detection results
      const updatedCar = {
        ...items.value[carIndex],
        actualPart: result.actual_part,
        outcome: result.outcome,
        isProcessing: false,
        image: result.original_image ? `data:image/jpeg;base64,${result.original_image}` : '',
        resultImage: result.result_image ? `data:image/jpeg;base64,${result.result_image}` : ''
      };
      
      // Update in items array
      items.value[carIndex] = updatedCar;
      
      // If this is the selected item, update it
      if (selectedItem.value && selectedItem.value.id === result.car_id) {
        selectedItem.value = updatedCar;
      }
      
      // Sort items to maintain order
      items.value = sortItems(items.value);
    }
    
    // Clear loading state
    isLoading.value = false;
    loadingMessage.value = '';
  });

  // Listen for detection errors
  socket.on('detection_error', (error: any) => {
    console.error('Detection error:', error);
    
    // Find the car in our list
    const carIndex = items.value.findIndex(item => item.id === error.car_id);
    if (carIndex !== -1) {
      // Update the car with error status
      const updatedCar = {
        ...items.value[carIndex],
        actualPart: "Error en detección",
        outcome: "Error",
        isProcessing: false
      };
      
      // Update in items array
      items.value[carIndex] = updatedCar;
      
      // If this is the selected item, update it
      if (selectedItem.value && selectedItem.value.id === error.car_id) {
        selectedItem.value = updatedCar;
      }
      
      // Sort items to maintain order
      items.value = sortItems(items.value);
    }
    
    // Clear loading state and show error
    isLoading.value = false;
    loadingMessage.value = '';
    errorMessage.value = `Error en la detección: ${error.error}`;
    setTimeout(() => errorMessage.value = '', 5000);
  });

  // Listen for new queued cars from GALC
  socket.on('new_queued_car', async (queuedCar: any) => {
    console.log('New queued car received:', queuedCar);
    items.value.push({
      id: queuedCar.car_id,
      expectedPart: queuedCar.expected_part,
      actualPart: '',
      outcome: '',
      image: '',
      resultImage: '',
      date: queuedCar.date,
      isQueued: true,
      isProcessing: false
    });
    // Sort items whenever a new car is added
    items.value = sortItems(items.value);
  });

  // Listen for auto-detection triggered events
  socket.on('auto_detection_triggered', (data: any) => {
    console.log('Auto-detection triggered for car:', data.car_id);
    
    // Clear any manual detection suggestion if auto-detection is now starting
    errorMessage.value = '';
    
    // Update loading message with car details
    loadingMessage.value = `Procesando detección automática para ${data.car_id}...`;
    isLoading.value = true;
    
    // Store or update the car ID as the active detection ID
    activeDetectionCarId.value = data.car_id;
    
    // Find the car in our list to show what we're detecting
    const carIndex = items.value.findIndex(item => item.id === data.car_id);
    if (carIndex !== -1) {
      // Ensure this car is selected so the user sees what's being processed
      // This is important for visibility in the footer
      selectedItem.value = items.value[carIndex];
      
      // Add a visual class to highlight this car in the footer
      // The CarsFooter component should react to selectedItem changes
      console.log('Selected item updated for detection:', selectedItem.value);
    } else {
      console.warn('Auto-detection triggered for unknown car:', data.car_id);
    }
  });

  // Listen for detection results
  socket.on('detection_result', async (data: any) => {
    console.log('Received detection result:', data);
    
    try {
        // Clear loading indicator if it's for the active detection car
        if (activeDetectionCarId.value === data.car_id) {
            loadingMessage.value = '';
            isLoading.value = false;
            activeDetectionCarId.value = null;
        }
        
        // Set the actual part based on detection results
        let actualPart = 'No hay capo';
        if (data.result?.objects && data.result.objects.length > 0) {
            // If we have detected objects, determine the type
            const hoodDetected = data.result.objects.some((obj: any) => 
                obj.class.toLowerCase().includes('capo') || obj.class.toLowerCase().includes('hood')
            );
            if (hoodDetected) {
                actualPart = data.result.is_capo_tipo_1 ? 'Capo tipo 1' : 'Capo tipo 2';
            }
        }
        
        // Fetch fresh data from the server to ensure we have the latest state
        const logs = await fetchLogs();
        console.log('Fetched updated logs:', logs);
        
        // Find the updated car in the fetched logs
        const updatedCar = logs.find((log: any) => log.car_id === data.car_id);
        if (!updatedCar) {
            console.warn('Could not find updated car in logs:', data.car_id);
            return;
        }
        
        // Create the updated car object with the fresh data
        const updatedItem = {
            id: updatedCar.car_id,
            expectedPart: updatedCar.expected_part,
            actualPart: actualPart,
            outcome: updatedCar.outcome,
            image: updatedCar.original_image ? `data:image/jpeg;base64,${updatedCar.original_image}` : '',
            resultImage: updatedCar.result_image ? `data:image/jpeg;base64,${updatedCar.result_image}` : '',
            date: updatedCar.date,
            grayPercentage: updatedCar.gray_percentage,
            isQueued: false,
            isProcessing: false
        };
        
        console.log('Updating car with fresh data:', updatedItem);
        
        // Update the car in our items list
        const index = items.value.findIndex(item => item.id === updatedItem.id);
        if (index !== -1) {
            items.value[index] = updatedItem;
        }
        
        // If this is the currently selected car, update the selected item
        if (selectedItem.value && selectedItem.value.id === updatedItem.id) {
            selectedItem.value = updatedItem;
        }
        
        // Sort items to maintain order
        items.value = sortItems(items.value);
        
        // Force a UI update
        await nextTick();
        
        // If outcome is NOGOOD and a hood was detected, send to ICS
        if (updatedItem.outcome === 'NOGOOD' && data.result?.hood_detected) {
            try {
                loadingMessage.value = 'Enviando datos a ICS...';
                await sendToICS({
                    car_id: updatedItem.id,
                    expected_part: updatedItem.expectedPart,
                    actual_part: updatedItem.actualPart,
                    outcome: updatedItem.outcome,
                    gray_percentage: updatedItem.grayPercentage,
                    image: updatedItem.image
                });
                console.log('Successfully sent data to ICS for car:', updatedItem.id);
            } catch (error) {
                console.error('Error sending to ICS:', error);
            } finally {
                loadingMessage.value = '';
            }
        }
    } catch (error) {
        console.error('Error processing detection result:', error);
        errorMessage.value = 'Error al procesar el resultado de la detección';
        setTimeout(() => errorMessage.value = '', 5000);
    }
  });

  // Fetch both logs and queued cars
  await Promise.all([
    fetchLogs().then((response: LogResponse[]) => {
      console.log('Fetched logs:', response);
      response.forEach((item: LogResponse) => {
        items.value.push({
          id: item.car_id,
          expectedPart: item.expected_part,
          actualPart: item.actual_part,
          outcome: item.outcome,
          image: item.original_image ? `data:image/jpeg;base64,${item.original_image}` : '',
          resultImage: item.result_image ? `data:image/jpeg;base64,${item.result_image}` : '',
          date: item.date,
          isQueued: false,
          isProcessing: false
        });
      });
    }),
    fetchQueuedCars().then((queuedCars) => {
      console.log('Fetched queued cars:', queuedCars);
      queuedCars.forEach((car: any) => {
        items.value.push({
          id: car.car_id,
          expectedPart: car.expected_part,
          actualPart: '',
          outcome: '',
          image: '',
          resultImage: '',
          date: car.date,
          isQueued: true,
          isProcessing: false
        });
      });
    })
  ]);

  // Sort all items after fetching
  items.value = sortItems(items.value);
});

onBeforeUnmount(() => {
  socket.off('connection_status');
  socket.off('connection_type');
  socket.off('plc_message');
  socket.off('handle_message');
  socket.off('new_car');
  socket.off('new_queued_car');
  socket.off('auto_detection_triggered');
  socket.off('detection_result');
});

const handleItemClicked = async (item: any) => {
  selectedItem.value = item;
  
  // If it's a queued car, just mark it as selected but don't process automatically
  if (item.isQueued) {
    // Only update the UI to show it's selected
    return;
  }
};

const handleClick = async () => {
  // Prevent multiple calls or calls without a selected item
  if (clickHandle || !selectedItem.value) {
    console.warn('handleClick ignored: already processing or no selectedItem');
    return;
  }
  
  // Set processing state
  clickHandle = true;
  isLoading.value = true;
  loadingMessage.value = 'Procesando imagen...';
  
  try {
    // Prepare car parameters
    const carParams = {
      car_id: selectedItem.value.id,
      expected_part: selectedItem.value.expectedPart,
      actual_part: selectedItem.value.actualPart || ''
    };

    // Capture image and get detection results
    const data = await captureImage(carParams) as CaptureResponse;
    
    if (!data) {
      throw new Error('No se recibieron datos de detección');
    }

    // Update UI with results
    const updatedItem = {
      ...selectedItem.value,
      image: data.image,  // Now using base64 data directly
      resultImage: data.resultImage,  // Now using base64 data directly
      grayPercentage: data.gray_percentage,
      outcome: data.is_capo_tipo_1 ? 'GOOD' : 'NOGOOD',
      actualPart: data.is_capo_tipo_1 ? 'Capo tipo 1' : 'No hay capo'
    };

    // Update selectedItem and items array
    selectedItem.value = updatedItem;
    const index = items.value.findIndex(item => item.id === updatedItem.id);
    if (index !== -1) {
      items.value[index] = updatedItem;
    }

    // Only send to ICS if outcome is NOGOOD and a hood was detected
    if (updatedItem.outcome === 'NOGOOD' && data.hood_detected) {
      try {
        loadingMessage.value = 'Enviando datos a ICS...';
        await sendToICS({
          car_id: updatedItem.id,
          expected_part: updatedItem.expectedPart,
          actual_part: updatedItem.actualPart,
          outcome: updatedItem.outcome,
          gray_percentage: updatedItem.grayPercentage,
          image: updatedItem.image  // Send base64 image directly
        });
      } catch (error) {
        console.error('Error sending to ICS:', error);
      }
    }

  } catch (error) {
    console.error('Error in handleClick:', error);
    errorMessage.value = 'Error durante el procesamiento: ' + (error instanceof Error ? error.message : 'Error desconocido');
    setTimeout(() => errorMessage.value = '', 5000);
  } finally {
    isLoading.value = false;
    loadingMessage.value = '';
    clickHandle = false;
  }
}

function esDefecto(item: any) {
  console.log("es defecto", item);
}
function noEsDefecto(item: any) {
  console.log("no es defecto", item);
}

const handleRetryConnection = async () => {
  if (isRetrying.value) return;
  
  isRetrying.value = true;
  try {
    await retryConnection();
  } catch (error) {
    console.error('Error retrying connection:', error);
  } finally {
    isRetrying.value = false;
  }
};

// Cleanup when component is unmounted
onUnmounted(() => {
  socket.off('connection_status');
  socket.off('connection_type');
  socket.off('plc_message');
  socket.off('handle_message');
  socket.off('new_car');
  socket.off('new_queued_car');
  socket.off('auto_detection_triggered');
  socket.off('detection_result');
});

// Process detection results and update UI accordingly
async function processDetectionResult(data: any) {
  if (!selectedItem.value) {
    console.warn('No selected item to update with detection results');
    return;
  }

  console.log('Processing detection result for car:', selectedItem.value.id);
  
  try {
    // Create a copy of the selected item to modify
    const updatedItem = { ...selectedItem.value };
    
    // Update image results
    if (data.image) {
      updatedItem.image = `data:image/jpeg;base64,${data.image}`;
    }
    if (data.result_image) {
      updatedItem.resultImage = `data:image/jpeg;base64,${data.result_image}`;
    }
    
    // Check for errors or warnings
    if (data.error) {
      errorMessage.value = data.error;
      console.error('Detection error:', data.error);
      
      // Still update the item with available information
      selectedItem.value = updatedItem;
      return;
    }
    
    if (data.warning) {
      console.warn('Detection warning:', data.warning);
    }
    
    // Extract object detection results
    const objects = data.objects || [];
    const detectedClasses = objects.map((obj: any) => obj.class);
    console.log('Detected objects:', detectedClasses);
    
    // Update with results from backend
    if (data.actual_part) {
      updatedItem.actualPart = data.actual_part;
    }
    
    if (data.outcome) {
      updatedItem.outcome = data.outcome;
    }
    
    // First update the selectedItem with what we have
    selectedItem.value = updatedItem;
    
    // Also update the item in the items array to maintain consistency
    const itemIndex = items.value.findIndex(item => item.id === updatedItem.id);
    if (itemIndex !== -1) {
      items.value[itemIndex] = updatedItem;
    } else {
      console.warn(`Could not find item with id ${updatedItem.id} in items array`);
    }
    
    // If NOGOOD outcome, send to ICS
    if (updatedItem.outcome === 'NOGOOD') {
      try {
        loadingMessage.value = 'Enviando datos a ICS...';
        await sendToICS({
          car_id: updatedItem.id,
          expected_part: updatedItem.expectedPart,
          actual_part: updatedItem.actualPart,
          outcome: updatedItem.outcome,
          gray_percentage: data.gray_percentage || 0
        });
        console.log('Successfully sent data to ICS');
      } catch (error) {
        console.error('Error sending to ICS:', error);
        // Continue with the flow even if ICS fails
      }
    }
  } catch (error) {
    console.error('Error processing detection result:', error);
    errorMessage.value = 'Error al procesar el resultado de la detección';
    setTimeout(() => errorMessage.value = '', 5000);
  } finally {
    loadingMessage.value = '';
  }
}

const detectObjects = async () => {
  if (!selectedItem.value) {
    console.error('Cannot detect objects - no car selected');
    errorMessage.value = 'Seleccione un vehículo primero';
    setTimeout(() => errorMessage.value = '', 3000);
    return;
  }
  
  if (isProcessing.value) {
    console.log('Already processing, ignoring additional detection request');
    return;
  }
  
  console.log('Starting detection for car:', selectedItem.value);
  
  isProcessing.value = true;
  errorMessage.value = '';
  loadingMessage.value = 'Procesando detección...';
  
  try {
    // Make sure we have a valid car ID and expected part
    if (!selectedItem.value.id) {
      throw new Error('Car ID missing');
    }
    
    if (!selectedItem.value.expectedPart) {
      throw new Error('Expected part missing');
    }
    
    // Build parameters for the capture request
    const captureParams = {
      car_id: selectedItem.value.id,
      expected_part: selectedItem.value.expectedPart,
      actual_part: selectedItem.value.actualPart || ''
    };
    
    console.log('Sending capture request with params:', captureParams);
    
    // Make the request to capture and detect
    const startTime = performance.now();
    const data = await captureImage(captureParams);
    const endTime = performance.now();
    console.log(`Detection completed in ${(endTime - startTime).toFixed(2)}ms`);
    console.log('Got detection result:', data);
    
    // Save the current selectedItem to verify it doesn't change during processing
    const originalSelectedItem = selectedItem.value;
    
    // Process the detection result
    await processDetectionResult(data);
    
    // Verify the selected item hasn't changed during processing
    if (selectedItem.value !== originalSelectedItem) {
      console.warn('Selected item changed during detection processing!');
    }
    
  } catch (error) {
    console.error('Error detecting objects:', error);
    errorMessage.value = 'Error al procesar la imagen: ' + (error instanceof Error ? error.message : 'Desconocido');
    setTimeout(() => errorMessage.value = '', 5000);
  } finally {
    isProcessing.value = false;
    loadingMessage.value = '';
  }
}

// Function to load the current configuration
const loadConfig = async () => {
  try {
    const config = await getConfig();
    console.log('Loaded configuration:', config);
  } catch (error) {
    console.error('Error loading configuration:', error);
  }
};
</script>

<style scoped>
.content {
  height: 100%;
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.connection-status {
  display: flex;
  align-items: center;
  height: min-content;
  background-color: var(--bg-300);
  padding: 10px 70px;
  color: var(--text-100);
  z-index: 1000;
}

.status-circle {
  width: 15px;
  height: 15px;
  border-radius: 50%;
  margin-right: 10px;
  background-color: var(--no-good-100);
  transition: background-color 0.3s ease;
}

.status-circle.connected {
  background-color: var(--good-100);
}

.connection-status {
  cursor: pointer
}

.container {
  overflow-y: auto;
  /* Enable vertical scrolling */
  background-color: var(--bg-100);
  padding: 0 15em;
  padding-top: 20px;
  color: #f5f5f5;
  font-family: sans-serif;
  gap: 10px;
}

.inspection-header {
  margin-top: 1rem;
  width: 100%;
  height: min-content;
  background-color: var(--bg-300);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 50px;
  border-radius: 20px;
  font-size: 1.4em;
}

.inspection-footer {
  width: 100%;
  height: 5em;
  background-color: var(--bg-300);
  display: flex;
  justify-content: space-around;
  align-items: center;
  margin-bottom: 20px;
  padding: 40px 50px;
  border-radius: 20px;
  font-size: 1.4em;
}

.no-item-selected {
  width: 100%;
  height: 100%;
  padding-bottom: 150px;
  background-color: var(--bg-300);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.4em;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}

.reload-icon {
  margin-left: 10px;
  width: 20px;
  height: 20px;
  cursor: pointer;
  transition: transform 0.3s ease;
  color: var(--text-100);
}

.reload-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.connection-status:hover .reload-icon:not(.spinning) {
  transform: rotate(90deg);
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  gap: 10px;
}

.loading-indicator svg {
  width: 24px;
  height: 24px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.error-message-container {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 80%;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  text-align: center;
  font-weight: bold;
}
</style>