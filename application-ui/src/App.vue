<template>
  <NavBar />
  <div class="container" v-if="selectedItem">
    <div class="inspection-header">
      <p>{{ selectedItem.id }}</p>
      <p>{{ selectedItem.name }}</p>
      <p>{{ selectedItem.date }}</p>
    </div>
    <div class="inspection-body">
      <!-- table with columns 'Status', 'Imagen Esperada', 'Imagen capturada' -->
      <table class="inspection-table">
        <thead>
          <th>Status</th>
          <th>Imagen Esperada</th>
          <th>Imagen capturada</th>
        </thead>
        <tbody>
          <tr>
            <td>{{ selectedItem.outcome }}</td>
            <td><img v-if="capturedImage" :src="capturedImage" alt="Captured Image" /></td>
            <td><img v-if="resultImage" :src="resultImage" alt="Result Image" /></td>
          </tr>
        </tbody>
      </table>
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
  <CarsFooter :items="items" v-model="selectedItem" />
</template>

<script lang="ts" setup>
import { useBackendApi } from './composables/useBackendApi'
import NavBar from './components/NavBar.vue'
import CarsFooter from './components/CarsFooter.vue'
import { ref } from 'vue';

const items = [
  { id: "058574", name: "T-Cross 1.0 COMFO", info: "128cv AGP, Rear view camera, Bluetooth", date: "2021-03-17 11:39:35", outcome: "success" },
  { id: "058486", name: "T-Cross 1.0 TPLUS", info: "125cv ASF, Front and side view cameras, Navigation", date: "2021-03-17 11:41:00", outcome: "success" },
  { id: "058672", name: "T-Cross 1.0 TURBO", info: "125cv A6F, Heated seats, Keyless entry", date: "2021-03-17 11:41:01", outcome: "success" },
  { id: "058659", name: "TCross 1.6 COMFO", info: "110cv AGF, Rear parking camera, Leather seats", date: "2021-03-17 11:41:02", outcome: "success" },
  { id: "058672", name: "T-Cross 1.0 COMFO XTREME", info: "125cv A6F, 360 degree camera, 4G connectivity", date: "2021-03-17 11:41:03", outcome: "success" },
  { id: "058659", name: "TCross 1.6 OMNI", info: "110cv AGF, Lane departure warning, 7-inch touchscreen", date: "2021-03-17 11:41:04", outcome: "success" },
  { id: "058659", name: "TCross 1.6 COMBO", info: "110cv AGF, Rear spoiler, Front fog lamps", date: "2021-03-17 11:41:05", outcome: "failure" },
  { id: "058659", name: "TCross 1.6 LUXURY", info: "110cv AGF, Leather steering wheel, Heated mirrors", date: "2021-03-17 11:41:06", outcome: "success" },
  { id: "058659", name: "TCross 1.6 SUPER", info: "110cv AGF, Rear view camera, Blind spot monitoring", date: "2021-03-17 11:41:07", outcome: "success" },
  { id: "058659", name: "TCross 1.6 ULTRA", info: "110cv AGF, Heated front seats, Adaptive cruise control", date: "2021-03-17 11:41:08", outcome: "success" },
];

const selectedItem = ref();

const { captureImage, capturedImage, detectedObjects, resultImage } = useBackendApi()

const handleClick = async () => {
  try {
    const data = await captureImage()
    console.log('Captured data:', data)
    capturedImage.value = `${data.image}`;
    detectedObjects.value = data.objects
    resultImage.value = `${data.resultImage}`
  } catch (error) {
    console.error('Error capturing data:', error)
    // Handle errors in the component
  }
}
</script>

<style scoped>
.container {
  height: 100%;
  background-color: var(--bg-100);
  padding: 0 70px;
  color: #f5f5f5;
  font-family: sans-serif;
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
  margin-top: 2rem;
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

.inspection-footer {
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
