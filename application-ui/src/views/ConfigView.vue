<template>
    <div class="config">
        <div class="config-content">
            <h1>Configuration</h1>

            <div class="umbral-input">
                <label for="umbral">Umbral (Threshold):</label>
                <input v-model="umbral" type="number" id="umbral" class="umbral" min="0.5" max="1.0" />
            </div>

            <button @click="handleSave" class="save-button">Save Configuration</button>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useBackendApi } from '../composables/useBackendApi'

const { getConfig, saveConfig } = useBackendApi();

const umbral = ref(0) // Initialize with a default value

onMounted(() => {
    getConfig().then((config) => {
        umbral.value = config.min_conf_threshold
    })
});

const handleSave = async () => {
    try {
        await saveConfig({ min_conf_threshold: umbral.value })
        alert('Configuration saved successfully!')
    } catch (error) {
        alert('Failed to save configuration.')
        console.error(error)
    }
}
</script>

<style scoped>
.config {
    min-height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    background-color: var(--bg-100);
}

.config-content {
    background: var(--bg-300);
    color: var(--text-100);
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
    text-align: center;
}

.umbral-input {
    margin-bottom: 20px;
    margin-top: 20px;
}

label {
    display: block;
    margin-bottom: 10px;
    font-weight: bold;
    text-align: left;
}

.umbral {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.save-button {
    background-color: var(--bg-200);
    color: white;
    padding: 10px 20px;
    border: var(--text-200) 2px solid;
    border-radius: 4px;
    cursor: pointer;
}

.save-button:hover {
    background-color: #45a049;
}

@media (min-width: 1024px) {
    .config {
        min-height: 100%;
        display: flex;
        align-items: center;
    }
}
</style>