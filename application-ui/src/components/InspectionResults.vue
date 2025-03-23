<template>
    <div class="inspection-results">
        <InspectionCard title="Imagen Resultante">
            <div v-if="modelValue?.warning" class="camera-warning">
                <p class="warning-text">⚠️ {{ modelValue.warning }}</p>
                <p class="warning-subtext">Se está utilizando una imagen de muestra</p>
            </div>
            <div v-else-if="modelValue?.using_placeholder" class="camera-warning">
                <p class="warning-text">⚠️ No se pudo acceder a la cámara</p>
                <p class="warning-subtext">Usando imagen de muestra para demostración</p>
            </div>
            <OutcomeImage v-if="modelValue?.resultImage" :imageSrc="modelValue.resultImage" />
            <div v-else class="no-image">
                <p>No hay imagen disponible</p>
            </div>
        </InspectionCard>
        <InspectionCard class="status" title="Estado" :style="getOutcomeStyle(modelValue?.outcome)">
            <div class="outcome">
                <br />
                <p>Esperado: {{ modelValue?.expectedPart || 'No especificado' }}</p>
                <br />
                <p>Resultado: {{ modelValue?.actualPart || 'Pendiente' }}</p>
            </div>
        </InspectionCard>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import InspectionCard from './InspectionCard.vue';
import OutcomeImage from './OutcomeImage.vue';

const props = defineProps({
    modelValue: {
        type: Object,
        default: () => ({})
    }
})
const modelValue = ref(props.modelValue);

watch(
    () => props.modelValue,
    (newValue) => {
        console.log('InspectionResults received new value:', newValue);
        modelValue.value = newValue;
        if (newValue?.grayPercentage !== undefined) {
            console.log(`Gray percentage: ${newValue.grayPercentage.toFixed(2)}%`);
        }
    },
    { immediate: true, deep: true }
);

function getOutcomeStyle(outcome: string) {
    if (!outcome) return 'background-color: var(--bg-300) !important';
    
    if (outcome === 'GOOD') {
        return 'background-color: var(--good-100) !important';
    } else if (outcome === 'NOGOOD') {
        return 'background-color: var(--no-good-100) !important';
    }
    return 'background-color: var(--bg-300) !important';
}
</script>

<style>
.inspection-results {
    width: 100%;
    height: min-content;
    min-height: 25em;
    font-size: 1.4em;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    align-items: center;
    justify-items: center;
    gap: 20px;
}

.status .outcome {
    height: 100%;
    padding-bottom: 8%;
    width: fit-content;
    margin: auto;
    font-weight: bold;
    font-size: 1.5em;
    text-transform: uppercase;
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: start;
}

.camera-warning {
    background-color: #fde1e1;
    border: 2px solid #ff6b6b;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 5px 20px 5px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.warning-text {
    color: #d32f2f;
    font-weight: bold;
    margin-bottom: 8px;
    font-size: 1.1em;
}

.warning-subtext {
    color: #616161;
    font-size: 0.9em;
}

.error-text {
    color: var(--no-good-100);
}

.error-message {
    font-size: 0.8em;
    display: block;
    margin-top: 5px;
}

.no-image {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 200px;
    background-color: var(--bg-200);
    color: var(--text-200);
    border-radius: 8px;
}
</style>