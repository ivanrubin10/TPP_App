<template>
  <div class="feedback-logs">
    <h1>Análisis de Feedback</h1>
    
    <div class="filters">
      <div class="filter-group">
        <label>Tipo de Feedback:</label>
        <select v-model="filterType">
          <option value="">Todos</option>
          <option value="false_positive">Falsos Positivos</option>
          <option value="false_negative">Falsos Negativos</option>
        </select>
      </div>
      <button class="filter-button" @click="fetchFeedbackLogs">Aplicar Filtros</button>
    </div>

    <div v-if="loading" class="loading">
      Cargando datos...
    </div>
    
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    
    <div v-else-if="feedbackLogs.length === 0" class="no-data">
      No se encontraron registros de feedback que coincidan con los filtros.
    </div>
    
    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Fecha</th>
            <th>Parte Esperada</th>
            <th>Parte Detectada</th>
            <th>Resultado Original</th>
            <th>Resultado Corregido</th>
            <th>Fecha de Feedback</th>
            <th>Nota</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in feedbackLogs" :key="item.id" 
              :class="{ 
                'false-positive': item.original_outcome === 'NOGOOD' && item.real_outcome === 'GOOD',
                'false-negative': item.original_outcome === 'GOOD' && item.real_outcome === 'NOGOOD'
              }">
            <td>{{ item.car_id }}</td>
            <td>{{ item.date }}</td>
            <td>{{ item.expected_part }}</td>
            <td>{{ item.actual_part }}</td>
            <td>{{ item.original_outcome }}</td>
            <td>{{ item.real_outcome }}</td>
            <td>{{ item.feedback_date }}</td>
            <td>{{ item.feedback_note }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="summary" v-if="feedbackLogs.length > 0">
      <h3>Resumen</h3>
      <p>Total de registros: {{ feedbackLogs.length }}</p>
      <p>Falsos positivos: {{ falsePositiveCount }}</p>
      <p>Falsos negativos: {{ falseNegativeCount }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useBackendApi } from '../composables/useBackendApi';

// Interfaz para los logs de feedback
interface FeedbackLog {
  id: number;
  car_id: string;
  date: string;
  expected_part: string;
  actual_part: string;
  original_image: string;
  result_image: string;
  original_outcome: string;
  real_outcome: string;
  feedback_note: string;
  feedback_date: string;
}

const backend = useBackendApi() as any;
const feedbackLogs = ref<FeedbackLog[]>([]);
const loading = ref<boolean>(false);
const error = ref<string>('');
const filterType = ref<string>(''); // 'false_positive', 'false_negative' o '' (todos)

// Estadísticas calculadas
const falsePositiveCount = computed(() => {
  return feedbackLogs.value.filter(
    log => log.original_outcome === 'NOGOOD' && log.real_outcome === 'GOOD'
  ).length;
});

const falseNegativeCount = computed(() => {
  return feedbackLogs.value.filter(
    log => log.original_outcome === 'GOOD' && log.real_outcome === 'NOGOOD'
  ).length;
});

async function fetchFeedbackLogs() {
  loading.value = true;
  error.value = '';
  
  try {
    const filters: { type?: string } = {};
    if (filterType.value) {
      filters.type = filterType.value;
    }
    
    const data = await backend.getFeedbackLogs(filters);
    feedbackLogs.value = data;
  } catch (err: any) {
    console.error('Error fetching feedback logs:', err);
    error.value = err.message || 'Error al cargar los datos de feedback';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchFeedbackLogs();
});
</script>

<style scoped>
.feedback-logs {
  padding: 2rem;
  background-color: var(--bg-100);
  min-height: calc(100vh - 83px);
  color: var(--text-100);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
  background-color: var(--bg-200);
  padding: 1rem;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-group label {
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.filter-group select, .filter-group input {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--bg-400);
  background-color: var(--bg-300);
  color: var(--text-100);
}

.filter-button {
  align-self: flex-end;
  padding: 0.5rem 1rem;
  background-color: var(--accent-100);
  color: var(--text-100);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.filter-button:hover {
  background-color: var(--accent-200);
}

.table-container {
  overflow-x: auto;
  margin-bottom: 2rem;
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

.false-positive {
  background-color: #4a6b8a; /* Color azulado para falsos positivos */
}

.false-negative {
  background-color: #8a4a4a; /* Color rojizo para falsos negativos */
}

.loading, .error, .no-data {
  padding: 2rem;
  text-align: center;
  background-color: var(--bg-200);
  border-radius: 8px;
  margin-bottom: 2rem;
}

.error {
  color: var(--no-good-100);
}

.summary {
  background-color: var(--bg-200);
  padding: 1.5rem;
  border-radius: 8px;
}

.summary h3 {
  margin-top: 0;
  margin-bottom: 1rem;
}

.summary p {
  margin: 0.5rem 0;
}
</style> 