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
            <tr v-for="item in store.items" :key="item.id" :class="{ 'good': item.outcome === 'GOOD', 'nogood': item.outcome === 'NOGOOD' }">
              <td>{{ item.id }}</td>
              <td>{{ item.date }}</td>
              <td>{{ item.expectedPart }}</td>
              <td>{{ item.actualPart }}</td>
              <td>{{ item.outcome }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { onMounted, onUnmounted } from 'vue';
  import { useAppStore } from '@/stores/useAppStore';
  
  const store = useAppStore();
  
  onMounted(async () => {
    await store.loadLogs();
  });
  
  // Force refresh data every minute
  let refreshInterval: number;
  onMounted(() => {
    refreshInterval = window.setInterval(() => {
      store.loadLogs(true);
    }, 60000);
  });
  
  onUnmounted(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });
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
  