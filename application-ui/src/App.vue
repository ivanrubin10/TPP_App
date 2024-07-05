<template>
  <NavBar />
  <div class="container" v-if="selectedItem">
    <div class="inspection-header">
      <p>{{ selectedItem.id }} - {{ selectedItem.name }}</p>
      <p>{{ selectedItem.date }}</p>
    </div>
    <div class="inspection-body">
      <div class="status">
        <p>Status</p>
        <div class="outcome" :style="getOutcomeStyle(selectedItem.outcome)">
          <p>
            {{ selectedItem.outcome }}
          </p>
        </div>
      </div>
      <div class="captured-image">
        <p>Imagen capturada</p>
        <img v-if="selectedItem.image" :src="selectedItem.image" alt="Captured Image" />
      </div>
      <div class="result-image">
        <p>Imagen Resultante</p>
        <img v-if="selectedItem.resultImage" :src="selectedItem.resultImage" alt="Result Image" />
      </div>
    </div>
    <div class="inspection-footer">
      <button>No es defecto</button>
      <button>Es defecto</button>
      <button @click="handleClick">Capture Image</button>
    </div>
    <!-- 

    <div class="results">
      <h1 v-if="detectedObjects.length">Results</h1>
      <div class="images">
        <div v-if="capturedImage" class="captured-image">
          <h3>Captured Image</h3>
          <img :src="capturedImage" alt="Captured Image" />
        </div>
        <div v-if="resultImage" class="result-image">
          <h3>Result Image</h3>
          <img :src="resultImage" alt="Result Image" />
        </div>
      </div>
      <div v-if="selectedItem" style="color: white; font-size: large;"> {{ selectedItem.id }}</div>
    </div> -->
    <!-- <pre v-if="detectedObjects.length">{{ JSON.stringify(detectedObjects, null, 2) }}</pre> -->
  </div>
  <div class="container" v-else>
    <div class="no-item-selected">
      Please select a car from the list to view its status
    </div>
  </div>
  <CarsFooter :items="items" v-model="selectedItem" @item-clicked="handleItemClicked" />
</template>

<script lang="ts" setup>
import { useBackendApi } from './composables/useBackendApi'
import NavBar from './components/NavBar.vue'
import CarsFooter from './components/CarsFooter.vue'
import { onMounted, ref } from 'vue';

const items = ref([
  { id: "058571", name: "T-Cross 1.0 COMFO", info: "128cv AGP, Rear view camera, Bluetooth", date: "2021-03-17 11:39:35", outcome: "success", image: "", resultImage: "" },
  { id: "058482", name: "T-Cross 1.0 TPLUS", info: "125cv ASF, Front and side view cameras, Navigation", date: "2021-03-17 11:41:00", outcome: "success", image: "", resultImage: "" },
  { id: "058673", name: "T-Cross 1.0 TURBO", info: "125cv A6F, Heated seats, Keyless entry", date: "2021-03-17 11:41:01", outcome: "success", image: "", resultImage: ""},
  { id: "058654", name: "TCross 1.6 COMFO", info: "110cv AGF, Rear parking camera, Leather seats", date: "2021-03-17 11:41:02", outcome: "success", image: "", resultImage: "" },
  { id: "058672", name: "T-Cross 1.0 COMFO XTREME", info: "125cv A6F, 360 degree camera, 4G connectivity", date: "2021-03-17 11:41:03", outcome: "success", image: "", resultImage: "" },
  { id: "058651", name: "TCross 1.6 OMNI", info: "110cv AGF, Lane departure warning, 7-inch touchscreen", date: "2021-03-17 11:41:04", outcome: "success", image: "", resultImage: "" },
  { id: "058652", name: "TCross 1.6 COMBO", info: "110cv AGF, Rear spoiler, Front fog lamps", date: "2021-03-17 11:41:05", outcome: "failure", image: "", resultImage: "" },
  { id: "058653", name: "TCross 1.6 LUXURY", info: "110cv AGF, Leather steering wheel, Heated mirrors", date: "2021-03-17 11:41:06", outcome: "success", image: "", resultImage: "" },
  { id: "058654", name: "TCross 1.6 SUPER", info: "110cv AGF, Rear view camera, Blind spot monitoring", date: "2021-03-17 11:41:07", outcome: "success", image: "", resultImage: "" },
  { id: "058655", name: "TCross 1.6 ULTRA", info: "110cv AGF, Heated front seats, Adaptive cruise control", date: "2021-03-17 11:41:08", outcome: "success", image: "", resultImage: "" },
]);

const fetchedItems = ref();

const selectedItem = ref();

const { captureImage,
    capturedImage,
    detectedObjects,
    resultImage,
    fetchLogs,
    logs,
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



function getOutcomeStyle(outcome: string) {
  if (outcome === 'success') {
    return 'background-image: linear-gradient(180deg, var(--good-100) 0%, var(--good-200) 100%)';
  } else if (outcome === 'failure') {
    return 'background-image: linear-gradient(180deg, var(--no-good-100) 0%, var(--no-good-200) 100%)';
  }
}
</script>

<style scoped>
.container {
  height: 100%;
  background-color: var(--bg-100);
  padding: 0 15em;
  color: #f5f5f5;
  font-family: sans-serif;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

img {
  max-width: 300px;
  max-height: 300px;
  object-fit: contain;
  margin-top: 15px;
}

.inspection-header {
  margin-top: 2rem;
  width: 100%;
  height: 6em;
  background-color: var(--bg-300);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 50px;
  border-radius: 20px;
  font-size: 1.4em;
}

.inspection-body {
  width: 100%;
  display: flex;
  gap: 20px;
  justify-content: space-between;
  align-items: center;
  border-radius: 20px;
  font-size: 1.4em;
}

.status {
  width: 100%;
  height: 11em;
  background-color: var(--bg-200);
  padding: 20px;
  border-radius: 20px;
  font-size: 1.4em;
}

.status p {
  text-align: center;
}

.status .outcome {
  height: 225px;
  width: 300px;
  object-fit: contain;
  margin: auto;
  margin-top: 15px;
  border-radius: 15px;
  background-color: var(--bg-300);
  font-weight: bold;
  font-size: 1.5em;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.captured-image {
  width: 100%;
  height: 11em;
  background-color: var(--bg-200);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0px;
  padding: 20px;
  border-radius: 20px;
  font-size: 1.4em;
}

.result-image {
  width: 100%;
  height: 11em;
  background-color: var(--bg-200);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
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
  padding: 0 50px;
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
