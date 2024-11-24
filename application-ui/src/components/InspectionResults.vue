<template>
    <div class="inspection-results">
        <InspectionCard title="Imagen Resultante">
            <OutcomeImage v-if="modelValue?.resultImage" :imageSrc="modelValue?.resultImage" />
        </InspectionCard>
        <InspectionCard class="status" title="Estado" :style="getOutcomeStyle(modelValue?.outcome)">
            <div class="outcome">
            <br />
                <p>Esperado: {{ modelValue?.expectedPart }}</p>
            <br />
                <p>Resultado: {{ modelValue?.actualPart }}</p>
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
        modelValue.value = newValue;
    },
    { immediate: true, deep: true }
);

function getOutcomeStyle(outcome: string) {
    if (outcome === 'success') {
        return 'background-image: linear-gradient(180deg, var(--good-100) 0%, var(--good-200) 100%)';
    } else if (outcome === 'failure') {
        return 'background-image: linear-gradient(180deg, var(--no-good-100) 0%, var(--no-good-200) 100%)';
    } else {
        return 'background-color: var(--bg-300)';
    }
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
</style>