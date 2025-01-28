<template>
  <div class="content">
    <div class="connection-status" @click="handleRetryConnection">
      <div class="status-circle" :class="{ 'connected': store.isConnected }"></div>
      <span>{{ store.connectionType }} {{ store.isConnected ? 'Conectado' : 'Desconectado' }}</span>
      <svg class="reload-icon" :class="{ 'spinning': store.isRetrying }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </div>
    
    <div class="container" v-if="store.selectedItem">
      <div class="inspection-header">
        <p>{{ store.selectedItem.id }}</p>
        <p>{{ store.selectedItem.date }}</p>
      </div>
      <InspectionResults v-model="store.selectedItem" />
      <div class="inspection-footer">
        <FalseOutcomeButton 
          v-if="!store.selectedItem.resultImage" 
          @click="handleInspectionClick" 
          text="Detectar" 
        />
        <FalseOutcomeButton 
          v-else 
          @click="handleInspectionClick" 
          text="Detectar nuevamente" 
        />
        <FalseOutcomeButton 
          v-show="store.selectedItem.outcome === 'NOGOOD'" 
          @click="handleNotDefect(store.selectedItem)"
          text="No es defecto" 
        />
        <FalseOutcomeButton 
          v-show="store.selectedItem.outcome === 'GOOD'" 
          @click="handleIsDefect(store.selectedItem)"
          text="Es defecto" 
        />
      </div>
    </div>
    <div class="container" v-else>
      <div class="no-item-selected">
        Por favor seleccione un coche de la lista para ver su estado
      </div>
    </div>
    
    <CarsFooter 
      :items="store.items" 
      v-model="store.selectedItem" 
      @item-clicked="handleItemClicked" 
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useAppStore } from '@/stores/useAppStore';
import { useWebSocket } from '@/composables/useWebSocket';
import { useInspection } from '@/composables/useInspection';
import type { CarItem } from '@/types';

import CarsFooter from '@/components/CarsFooter.vue';
import FalseOutcomeButton from '@/components/FalseOutcomeButton.vue';
import InspectionResults from '@/components/InspectionResults.vue';

const store = useAppStore();
const { handleInspection, isProcessing } = useInspection();
const { emit } = useWebSocket();

// Load data immediately
store.loadLogs();

// Declare refresh interval
let refreshInterval: number;

onMounted(() => {
  // Set up auto-refresh
  refreshInterval = window.setInterval(() => {
    store.loadLogs(true);
  }, 30000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});

const handleItemClicked = async (item: CarItem) => {
  store.setSelectedItem(item);
};

const handleInspectionClick = async () => {
  if (!store.selectedItem || isProcessing.value) return;
  
  try {
    const updatedItem = await handleInspection(store.selectedItem);
    if (updatedItem) {
      // Send response to PLC if needed
      if (store.connectionType === 'PLC') {
        emit('plc_response', { 
          message: updatedItem.actualPart === updatedItem.expectedPart ? 'GOOD' : 'NOGOOD' 
        });
      }
    }
  } catch (error) {
    console.error('Error during inspection:', error);
  }
};

const handleRetryConnection = async () => {
  if (store.isRetrying) return;
  store.setRetrying(true);
  try {
    await store.retryConnection();
  } finally {
    store.setRetrying(false);
  }
};

const handleIsDefect = (item: CarItem) => {
  console.log("es defecto", item);
};

const handleNotDefect = (item: CarItem) => {
  console.log("no es defecto", item);
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
  cursor: pointer;
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

.container {
  overflow-y: auto;
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
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.connection-status:hover .reload-icon:not(.spinning) {
  transform: rotate(90deg);
}
</style>