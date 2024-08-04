<template>
<div class="container" v-if="selectedItem">
    <div class="inspection-header">
      <p>{{ selectedItem.id }} - {{ selectedItem.name }}</p>
      <p>{{ selectedItem.date }}</p>
    </div>
    <InspectionResults v-model="selectedItem"/>
    <div class="inspection-footer">
      <FalseOutcomeButton @click="noEsDefecto(selectedItem)" text="No es defecto"/>
      <FalseOutcomeButton @click="esDefecto(selectedItem)" text="Es defecto"/>
      <button @click="handleClick">Capture Image</button>
    </div>
  </div>
  <div class="container" v-else>
    <div class="no-item-selected">
      Please select a car from the list to view its status
    </div>
  </div>
  <CarsFooter :items="items" v-model="selectedItem" @item-clicked="handleItemClicked" />
</template>


<script lang="ts" setup>
import { useBackendApi } from '../composables/useBackendApi'
import CarsFooter from '../components/CarsFooter.vue'
import FalseOutcomeButton from '../components/FalseOutcomeButton.vue'
import InspectionResults from '../components/InspectionResults.vue'
import { onMounted, ref } from 'vue';

const items = ref([
  { id: "058571", name: "T-Cross 1.0 COMFO", expectedPart: "Capo tipo 1", info: "128cv AGP, Rear view camera, Bluetooth", date: "2021-03-17 11:39:35", outcome: "success", image: "", resultImage: "" },
  { id: "058482", name: "T-Cross 1.0 TPLUS", expectedPart: "Capo tipo 2", info: "125cv ASF, Front and side view cameras, Navigation", date: "2021-03-17 11:41:00", outcome: "success", image: "", resultImage: "" },
  { id: "058673", name: "T-Cross 1.0 TURBO", expectedPart: "Capo tipo 3", info: "125cv A6F, Heated seats, Keyless entry", date: "2021-03-17 11:41:01", outcome: "success", image: "", resultImage: ""},
  { id: "058654", name: "TCross 1.6 COMFO", expectedPart: "Capo tipo 2", info: "110cv AGF, Rear parking camera, Leather seats", date: "2021-03-17 11:41:02", outcome: "success", image: "", resultImage: "" },
  { id: "058672", name: "T-Cross 1.0 COMFO XTREME", expectedPart: "Capo tipo 1", info: "125cv A6F, 360 degree camera, 4G connectivity", date: "2021-03-17 11:41:03", outcome: "success", image: "", resultImage: "" },
  { id: "058651", name: "TCross 1.6 OMNI", expectedPart: "Capo tipo 3", info: "110cv AGF, Lane departure warning, 7-inch touchscreen", date: "2021-03-17 11:41:04", outcome: "success", image: "", resultImage: "" },
  { id: "058652", name: "TCross 1.6 COMBO", expectedPart: "Capo tipo 3", info: "110cv AGF, Rear spoiler, Front fog lamps", date: "2021-03-17 11:41:05", outcome: "failure", image: "", resultImage: "" },
  { id: "058653", name: "TCross 1.6 LUXURY", expectedPart: "Capo tipo 2", info: "110cv AGF, Leather steering wheel, Heated mirrors", date: "2021-03-17 11:41:06", outcome: "success", image: "", resultImage: "" },
  { id: "058654", name: "TCross 1.6 SUPER", expectedPart: "Capo tipo 2", info: "110cv AGF, Rear view camera, Blind spot monitoring", date: "2021-03-17 11:41:07", outcome: "success", image: "", resultImage: "" },
  { id: "058655", name: "TCross 1.6 ULTRA", expectedPart: "Capo tipo 1", info: "110cv AGF, Heated front seats, Adaptive cruise control", date: "2021-03-17 11:41:08", outcome: "success", image: "", resultImage: "" },
]);

const fetchedItems = ref();

const selectedItem = ref();

const { captureImage,
    detectedObjects,
    fetchLogs,
    checkCarExists,
    updateItem,
    addLog  } = useBackendApi()

onMounted(async () => {
  await fetchLogs().then((response) => {
    fetchedItems.value = response;
    items.value.forEach((item) => {
      const foundItem = fetchedItems.value.find((fetchedItem: { car_id: string; }) => fetchedItem.car_id === item.id);
      if (foundItem) {
        item.image = foundItem.original_image_path;
        item.resultImage = foundItem.result_image_path;
      }
    });
  });
  console.log("fetched: ", fetchedItems.value[0])
  // assign the images to the items
  
});

const handleItemClicked = (item: any) => {
  selectedItem.value = item;
};

const handleClick = async () => {
  try {
    const data = await captureImage();
    console.log('Captured data:', data);

    selectedItem.value.image  = data.image;
    detectedObjects.value = data.objects;
    selectedItem.value.resultImage = data.resultImage;

    const carId = selectedItem.value.id;

    // Check if the car exists in the database
    const carExists = await checkCarExists(carId);

    if (carExists.exists) {
      // Update the existing log with new images and status
      const itemToUpdate = {
        id: carExists.car_log.id,
        car_id: carId,
        car_info: selectedItem.value.info,
        // Assuming image paths are stored in the database:
        original_image_path: data.image, // Update original image path if needed
        result_image_path: data.resultImage, // Update result image path
        outcome: selectedItem.value.outcome,
      };
      await updateItem(itemToUpdate);
    } else {
      // Add a new log with captured images and status
      const newLog = {
        car_id: carId,
        car_info: selectedItem.value.info,
        original_image_path: data.image, // Store the new image path
        result_image_path: data.resultImage, // Store the new result image path
        outcome: selectedItem.value.outcome,
      };
      await addLog(newLog);
    }
  } catch (error) {
    console.error('Error capturing data:', error);
  }
};

function esDefecto(item: any) {
  console.log("es defecto", item);
}
function noEsDefecto(item: any) {
  console.log("no es defecto", item);
}

</script>

<style scoped>
.container {
  height: 80vh;
  overflow-y: auto; /* Enable vertical scrolling */
  background-color: var(--bg-100);
  padding: 0 15em;
  padding-top: 50px;
  margin-top: 4em;
  color: #f5f5f5;
  font-family: sans-serif;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.inspection-header {
  margin-top: 2rem;
  width: 100%;
  height: min-content;
  background-color: var(--bg-300);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 50px 50px;
  border-radius: 20px;
  font-size: 1.4em;
}

.inspection-footer {
  width: 100%;
  height: 6em;
  background-color: var(--bg-300);
  display: flex;
  justify-content: space-evenly;
  align-items: center;
  margin-bottom: 100px;
  padding: 50px 50px;
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