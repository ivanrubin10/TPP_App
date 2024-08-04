<template>
    <div class="inspection-results">
        <InspectionCard title="Imagen Resultante">
            <div class="inspection-image">
                <img v-if="modelValue?.resultImage" :src="modelValue?.resultImage" alt="Result Image" />
            </div>
        </InspectionCard>
        <InspectionCard class="status" title="Status" :style="getOutcomeStyle(modelValue?.outcome)">
            <div class="outcome">
            <br />
                <p>expected: {{ modelValue?.expectedPart }}</p>
            <br />
                <p>result: {{ modelValue?.actualPart }}</p>
            </div>
        </InspectionCard>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import InspectionCard from './InspectionCard.vue';

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
    }
}
</script>

<style>
.inspection-results {
    display: flex;
    flex-direction: row;
    gap: 20px;
    width: 100%;
    height: min-content;
    min-height: 25em;
    justify-content: space-evenly;
    align-items: center;
    font-size: 1.4em;
}

.inspection-image {
    height: 90%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 20px;
}

img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
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