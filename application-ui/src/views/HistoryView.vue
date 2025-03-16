<template>
    <div class="historial">
      <h1>Historial</h1>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Fecha</th>
              <th>Parte Esperada</th>
              <th>Parte Resultante</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" :class="{ 'good': item.outcome === 'GOOD', 'nogood': item.outcome === 'NOGOOD' }">
              <td>{{ (item as any).id }}</td>
              <td>{{ (item as any).date }}</td>
              <td>{{ (item as any).expectedPart }}</td>
              <td>{{ (item as any).actualPart }}</td>
              <td>{{ (item as any).outcome }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { useBackendApi } from '../composables/useBackendApi'
  import { onMounted, ref } from 'vue';
  
  const items = ref<Item[]>([]);
  
  const {
    fetchLogs,
  } = useBackendApi()
  
  type Item = {
    id: string;
    expectedPart: string;
    actualPart: string;
    outcome: string;
    image: string;
    resultImage: string;
    date: string;
  }
  
  onMounted(() => {
    fetchLogs().then((response) => {
      console.log(response);
      items.value = response.map((item: any): Item => ({
        id: item.car_id,
        expectedPart: item.expected_part,
        actualPart: item.actual_part,
        outcome: item.outcome,
        image: item.original_image,
        resultImage: item.result_image,
        date: item.date
      } as Item));
    });
  })
  </script>
  
  <style>
  .historial {
    padding: 2rem;
    background-color: var(--bg-100);
  }
  
  .table-container {
    margin-top: 2rem;
    overflow-x: auto;
    color: var(--text-100);
  }
  
  h1 {
    color: var(--text-100);
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    background-color: var(--bg-200);
  }
  
  th, td {
    padding: 1rem;
    text-align: left;
    border-bottom: 1px solid var(--accent-200);
  }
  
  th {
    background-color: var(--bg-300);
    font-weight: bold;
  }
  
  tr {
    background-color: var(--bg-300);
  }
  
  tr.good {
    background-color: var(--good-100);
  }
  
  tr.nogood {
    background-color: var(--no-good-100);
  }
  
  @media (min-width: 1024px) {
    .dashboard {
      min-height: 100vh;
    }
  }
  </style>
  