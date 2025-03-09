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
        <FalseOutcomeButton v-if="!selectedItem.resultImage" @click="handleClick" text="Detectar" />
        <FalseOutcomeButton v-else @click="handleClick" text="Detectar nuevamente" />
        <FalseOutcomeButton v-show="selectedItem.outcome === 'NOGOOD'" @click="noEsDefecto(selectedItem)"
          text="No es defecto" />
        <FalseOutcomeButton v-show="selectedItem.outcome === 'GOOD'" @click="esDefecto(selectedItem)"
          text="Es defecto" />
      </div>
    </div>
    <div class="container" v-else>
      <div class="no-item-selected">
        Por favor seleccione un coche de la lista para ver su estado
      </div>
    </div>
    <CarsFooter :items="items" v-model="selectedItem" @item-clicked="handleItemClicked" />
  </div>
</template>


<script lang="ts" setup>
import { useBackendApi } from '../composables/useBackendApi'
import CarsFooter from '../components/CarsFooter.vue'
import FalseOutcomeButton from '../components/FalseOutcomeButton.vue'
import InspectionResults from '../components/InspectionResults.vue'
import { onBeforeUnmount, onMounted, ref } from 'vue';
import socket from '../composables/socket';
import axios from 'axios';

const baseUrl = 'http://localhost:5000'

type Item = {
  id: string;
  expectedPart: string;
  actualPart: string;
  outcome: string;
  image: string;
  resultImage: string;
  date: string;
  isQueued: boolean;
  grayPercentage?: number;
}

interface LogResponse {
  car_id: string;
  expected_part: string;
  actual_part: string;
  outcome: string;
  original_image_path: string;
  result_image_path: string;
  date: string;
}

const items = ref<Item[]>([]);
const isConnected = ref(false);
const connectionType = ref('PLC');
const messageBeingHandled = ref(false);


const selectedItem = ref();

const { captureImage,
  detectedObjects,
  fetchLogs,
  checkCarExists,
  updateItem,
  addLog,
  retryConnection,
  sendToICS,
  getConfig } = useBackendApi()

let clickHandle = false;

const isRetrying = ref(false);

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

onMounted(async () => {
  // Get initial config to set connection type
  const config = await getConfig();
  connectionType.value = config.connection_type;

  socket.on('connection_status', (data: any) => {
    isConnected.value = data.status;
  });

  socket.on('connection_type', (data: any) => {
    connectionType.value = data.type;
  });
  
  socket.on('plc_message', async (data: any) => {
    console.log(`Received message from PLC:`, data.message);
    await handleMessage(data, 'plc');
  });

  socket.on('handle_message', async (data: any) => {
    if (messageBeingHandled.value) {
      console.warn('Message handling is already in progress. Ignoring this message.');
      return;
    }
    
    messageBeingHandled.value = true;
    try {
      console.log(`Received message from GALC:`, data.message);
      await handleMessage(data, 'galc').then(() => {
        messageBeingHandled.value = false;
      });
    } catch (error) {
      console.error('Error handling message:', error);
    } finally {
      messageBeingHandled.value = false; // Reset the flag after processing
    }
  });

  // Listen for new queued cars from GALC
  socket.on('new_queued_car', async (queuedCar: any) => {
    console.log('Received new queued car:', queuedCar);
    items.value.push({
      id: queuedCar.car_id,
      expectedPart: queuedCar.expected_part,
      actualPart: '',
      outcome: '',
      image: '',
      resultImage: '',
      date: queuedCar.date,
      isQueued: true
    });
    // Sort items whenever a new car is added
    items.value = sortItems(items.value);
  });

  let isProcessing = false;

  async function handleMessage(data: any, type: 'plc' | 'galc') {
    if (isProcessing) {
      console.warn('Message handling is already in progress. Ignoring this message.');
      return;
    }
    
    isProcessing = true;
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

      // For PLC, process immediately. For GALC, this won't be called as we're using the queue system
      if (type === 'plc') {
        const newItem = {
          car_id: Math.random().toString(36).slice(2, 8),
          date: formattedDate,
          expected_part: expectedPart,
          actual_part: '',
          original_image_path: '',
          result_image_path: '',
          outcome: ''
        };

        await addLog(newItem);

        items.value.push({
          id: newItem.car_id,
          expectedPart: newItem.expected_part,
          actualPart: newItem.actual_part,
          outcome: newItem.outcome,
          image: newItem.original_image_path,
          resultImage: newItem.result_image_path,
          date: newItem.date,
          isQueued: false
        });
        
        selectedItem.value = items.value[items.value.length - 1];
        await handleClick();

        socket.emit('plc_response', { message: expectedPart === selectedItem.value.actualPart ? 'GOOD' : 'NOGOOD' });
      }
    } finally {
      isProcessing = false;
    }
  }

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
          image: item.original_image_path,
          resultImage: item.result_image_path,
          date: item.date,
          isQueued: false
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
          isQueued: true
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
  socket.off('handle_message');
  socket.off('new_queued_car');
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
  if (clickHandle) return;
  clickHandle = true;
  try {
    const carParams = selectedItem.value ? {
      car_id: selectedItem.value.id,
      expected_part: selectedItem.value.expectedPart,
      actual_part: selectedItem.value.actualPart
    } : null;

    const data = await captureImage(carParams);
    console.log('Raw response from capture:', data);

    if (data.error === "No hay capo") {
      selectedItem.value.actualPart = "No hay capo";
      selectedItem.value.outcome = "NOGOOD";
      selectedItem.value.grayPercentage = data.gray_percentage;
      console.log('Gray percentage too low:', data.gray_percentage);
    } else {
      selectedItem.value.image = data.image;
      selectedItem.value.resultImage = data.resultImage;
      selectedItem.value.grayPercentage = data.gray_percentage;
      console.log('Gray percentage:', data.gray_percentage);

      if (detectedObjects.value.length === 0) {
        selectedItem.value.actualPart = "No hay capo";
        selectedItem.value.outcome = "NOGOOD";
      } else if (detectedObjects.value.length === 2) {
        selectedItem.value.actualPart = "Capo tipo 1";
        selectedItem.value.outcome = selectedItem.value.expectedPart === "Capo tipo 1" ? "GOOD" : "NOGOOD";
      } else if (detectedObjects.value.length === 3) {
        selectedItem.value.actualPart = "Capo tipo 2";
        selectedItem.value.outcome = selectedItem.value.expectedPart === "Capo tipo 2" ? "GOOD" : "NOGOOD";
      }

      // If connection type is GALC and outcome is NOGOOD, send to ICS
      if (connectionType.value === 'GALC' && selectedItem.value.outcome === 'NOGOOD') {
        await sendToICS({
          car_id: selectedItem.value.id,
          expected_part: selectedItem.value.expectedPart,
          actual_part: selectedItem.value.actualPart,
          outcome: selectedItem.value.outcome,
          gray_percentage: selectedItem.value.grayPercentage
        });
      }

      // Check if car exists in database
      const exists = await checkCarExists(selectedItem.value.id);
      if (exists) {
        // Update existing log
        await updateItem({
          car_id: selectedItem.value.id,
          expected_part: selectedItem.value.expectedPart,
          actual_part: selectedItem.value.actualPart,
          outcome: selectedItem.value.outcome,
          original_image_path: selectedItem.value.image,
          result_image_path: selectedItem.value.resultImage,
          gray_percentage: selectedItem.value.grayPercentage
        });
      } else {
        // Add new log
        await addLog({
          car_id: selectedItem.value.id,
          expected_part: selectedItem.value.expectedPart,
          actual_part: selectedItem.value.actualPart,
          outcome: selectedItem.value.outcome,
          original_image_path: selectedItem.value.image,
          result_image_path: selectedItem.value.resultImage,
          gray_percentage: selectedItem.value.grayPercentage
        });
      }

      // If this was a queued car, mark it as processed
      if (selectedItem.value.isQueued) {
        await processQueuedCar(selectedItem.value.id);
        selectedItem.value.isQueued = false;
      }
    }
  } catch (error) {
    console.error('Error in handleClick:', error);
  } finally {
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
</style>