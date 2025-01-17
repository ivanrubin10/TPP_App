<template>
  <div class="content">
    <div class="connection-status" @click="retryConnection">
      <div class="status-circle" :class="{ 'connected': isConnected }"></div>
      <span>{{ isConnected ? `${connectionType} Conectado` : `${connectionType} Desconectado` }}</span>
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


type Item = {
  id: string;
  expectedPart: string;
  actualPart: string;
  outcome: string;
  image: string;
  resultImage: string;
  date: string;
}

const items = ref<Item[]>([]);
const isConnected = ref(false);
const connectionType = ref('PLC');
const messageBeingHandled = ref(false);

const fetchedItems = ref();
const selectedItem = ref();

const { captureImage,
  detectedObjects,
  fetchLogs,
  checkCarExists,
  updateItem,
  addLog,
  retryConnection,
 } = useBackendApi()

onMounted(async () => {
  socket.on('connection_status', (data: any) => {
    isConnected.value = data.status;
  }
  );

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
        date: newItem.date
      });
      
      selectedItem.value = items.value[items.value.length - 1];
      await handleClick();

      const response_message = expectedPart === selectedItem.value.actualPart ? 'GOOD' : 'NOGOOD';
      if (type === 'plc') {
        socket.emit('plc_response', { message: response_message });
      } else if (type === 'galc') {
        socket.emit('galc_response', { message: response_message });
      }
    } finally {
      isProcessing = false;
    }
  }

  await fetchLogs().then((response) => {
    console.log(response);
    fetchedItems.value = response;
    response.forEach((item: any) => {
      items.value.push({
        id: item.car_id,
        expectedPart: item.expected_part,
        actualPart: item.actual_part,
        outcome: item.outcome,
        image: item.original_image_path,
        resultImage: item.result_image_path,
        date: item.date,
      });
    })
    items.value.forEach((item) => {
      const foundItem = fetchedItems.value.find((fetchedItem: { car_id: string; }) => fetchedItem.car_id === item.id);
      if (foundItem) {
        item.image = foundItem.original_image_path;
        item.resultImage = foundItem.result_image_path;
        item.outcome = foundItem.outcome;
        item.actualPart = foundItem.actual_part;
        item.date = foundItem.date;
      }
    });
  });
  console.log("fetched: ", fetchedItems.value)
  // assign the images to the items

});

onBeforeUnmount(() => {
  // Clean up the event listeners when the component is unmounted
  socket.off('connection_status');
  socket.off('connection_type');
  socket.off('handle_message');
});

const handleItemClicked = (item: any) => {
  selectedItem.value = item;
};

let clickHandle = false;
const handleClick = async () => {
  if (clickHandle) {
    return;
  }

  clickHandle = true;
  try {
    const data = await captureImage();
    console.log('Captured data:', data);

    const currentDate = new Date();
    selectedItem.value.date = `${currentDate.getDate()}-${currentDate.getMonth() + 1}-${currentDate.getFullYear()} ${currentDate.getHours()}:${currentDate.getMinutes()}:${currentDate.getSeconds()}`;
    selectedItem.value.image = data.image;
    detectedObjects.value = data.objects;
    selectedItem.value.resultImage = data.resultImage;

    if (data.objects.length === 0) {
      selectedItem.value.actualPart = "Capo tipo 1";
    } else if (data.objects.length === 2) {
      selectedItem.value.actualPart = "Capo tipo 2";
    } else if (data.objects.length === 3) {
      selectedItem.value.actualPart = "Capo tipo 3";
    } else {
      selectedItem.value.actualPart = "";
    }
    console.log("actualPart: ", selectedItem.value.actualPart);

    if (selectedItem.value.actualPart === selectedItem.value.expectedPart) {
      selectedItem.value.outcome = "GOOD";
    } else {
      selectedItem.value.outcome = "NOGOOD";
    }
    const carId = selectedItem.value.id;

    // Check if the car exists in the database
    const carExists = await checkCarExists(carId);

    if (carExists.exists) {
      // Update the existing log with new images and status
      const itemToUpdate = {
        id: carExists.car_log.id,
        car_id: carId,
        date: selectedItem.value.date,
        expected_part: selectedItem.value.expectedPart,
        actual_part: selectedItem.value.actualPart,
        original_image_path: data.image, // Update original image path if needed
        result_image_path: data.resultImage, // Update result image path
        outcome: selectedItem.value.outcome,
      };
      await updateItem(itemToUpdate);
    } else {
      // Add a new log with captured images and status
      const newLog = {
        car_id: carId,
        date: selectedItem.value.date,
        expected_part: selectedItem.value.expectedPart,
        actual_part: selectedItem.value.actualPart,
        original_image_path: data.image, // Store the new image path
        result_image_path: data.resultImage, // Store the new result image path
        outcome: selectedItem.value.outcome,
      };
      await addLog(newLog);
    }
  } catch (error) {
    console.error('Error capturing data:', error);
  }

  clickHandle = false;
};

function esDefecto(item: any) {
  console.log("es defecto", item);
}
function noEsDefecto(item: any) {
  console.log("no es defecto", item);
}
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
</style>