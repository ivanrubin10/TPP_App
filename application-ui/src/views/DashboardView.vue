<template>
    <div class="dashboard">
        <h1>Dashboard</h1>

        <div class="dashboard-grid">
            <!-- Summary Cards -->
            <div class="summary-card">
                <h3>Inspecciones totales</h3>
                <div class="stat">{{ store.items.length }}</div>
            </div>
            <div class="summary-card">
                <h3>Tasa de éxito</h3>
                <div class="stat">{{ store.successRate }}%</div>
            </div>
            <div class="summary-card">
                <h3>Tasa de fallos</h3>
                <div class="stat">{{ 100 - store.successRate }}%</div>
            </div>

            <!-- Charts -->
            <div class="chart-container" @click="openModal('pie')">
                <h3>Resultados de inspección</h3>
                <Pie :data="pieChartData" :options="baseChartOptions" />
            </div>

            <div class="chart-container" @click="openModal('line')">
                <h3>Inspecciones diarias</h3>
                <Line :data="lineChartData" :options="lineChartOptions" />
            </div>

            <!-- Table -->
            <div class="table-container">
                <h3>Inspecciones recientes</h3>
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
                        <tr v-for="item in store.items.slice(0, 10)" :key="item.id"
                            :class="{ 'good': item.outcome === 'GOOD', 'nogood': item.outcome === 'NOGOOD' }">
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

        <!-- Modal -->
        <div v-if="showModal" class="modal" @click="closeModal">
            <div class="modal-content" @click.stop>
                <span class="close" @click="closeModal">&times;</span>
                <div class="modal-chart">
                    <h3>{{ selectedChart === 'pie' ? 'Resultados de inspección' : 'Inspecciones diarias' }}</h3>
                    <Pie v-if="selectedChart === 'pie'" :data="pieChartData" :options="modalChartOptions.pie" />
                    <Line v-if="selectedChart === 'line'" :data="lineChartData" :options="modalChartOptions.line" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement } from 'chart.js';
import { Pie, Line } from 'vue-chartjs';
import { useAppStore } from '@/stores/useAppStore';
import { useCharts } from '@/composables/useCharts';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement);

const store = useAppStore();
const showModal = ref(false);
const selectedChart = ref('');

const {
    pieChartData,
    lineChartData,
    baseChartOptions,
    lineChartOptions,
    modalChartOptions
} = useCharts(store.items);

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

const openModal = (chartType: string) => {
    selectedChart.value = chartType;
    showModal.value = true;
};

const closeModal = () => {
    showModal.value = false;
};
</script>

<style>
.dashboard {
    padding: 2rem;
    background-color: var(--bg-100);
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.summary-card {
    background-color: var(--bg-400);
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.summary-card h3 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
    color: var(--text-100);
}

.summary-card .stat {
    font-size: 2rem;
    font-weight: bold;
    margin-top: 0.5rem;
    color: var(--accent-200);
}

.chart-container {
    background-color: var(--bg-400);
    padding: 1.5rem;
    border-radius: 8px;
    height: 300px;
    position: relative;
    cursor: pointer;
    transition: transform 0.2s;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.chart-container h3 {
    color: var(--text-100);
    margin-bottom: 0.5rem;
}

.chart-container:hover {
    transform: scale(1.02);
}

.table-container {
    grid-column: 1 / -1;
    background-color: var(--bg-400);
    padding: 1.5rem;
    border-radius: 8px;
    overflow-x: auto;
    justify-content: center;
}

.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background-color: var(--bg-400);
    padding: 2rem;
    border-radius: 8px;
    width: 80%;
    max-width: 800px;
    position: relative;
}

.modal-content h3 {
    color: var(--text-100);
    margin-bottom: 1rem;
}

.modal-chart {
    height: 60vh;
}

.close {
    position: absolute;
    right: 1rem;
    top: 0.5rem;
    font-size: 2rem;
    cursor: pointer;
    color: var(--text-100);
}

h1 {
    margin-bottom: 1rem;
    color: var(--text-100);
}

h3 {
    margin-bottom: 1rem;
}

table {
    width: 100%;
    border-collapse: collapse;
    background-color: var(--bg-200);
}

.table-container h3 {
    color: var(--text-100);
}

th,
td {
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
    color: var(--text-100);
}

tr.good {
    background-color: var(--good-100);
}

tr.nogood {
    background-color: var(--no-good-100);
}

@media (min-width: 1024px) {
    .dashboard {
        min-height: 100%;
    }
}
</style>
