<template>
  <div class="image-source-selector">
    <div class="selector-title">Fuente de imagen:</div>
    <div class="selector-options">
      <div 
        v-for="option in options" 
        :key="option.value" 
        class="option" 
        :class="{ 'selected': modelValue === option.value }"
        @click="$emit('update:modelValue', option.value)"
      >
        {{ option.label }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  }
});

defineEmits(['update:modelValue']);

const options = [
  { value: 'camera', label: 'Cámara' },
  { value: 'no_capo', label: 'No Capo' },
  { value: 'capo_tipo_1', label: 'Capo Tipo 1' },
  { value: 'capo_tipo_2', label: 'Capo Tipo 2' },
  { value: 'capo_tipo_3', label: 'Capo Tipo 3' }
];
</script>

<style scoped>
.image-source-selector {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-300);
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 15px;
}

.selector-title {
  font-size: 1.1em;
  margin-bottom: 10px;
  color: var(--text-100);
}

.selector-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.option {
  padding: 8px 15px;
  background-color: var(--bg-200);
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-100);
}

.option:hover {
  background-color: var(--bg-100);
}

.option.selected {
  background-color: var(--good-100);
  color: var(--bg-300);
  font-weight: bold;
}
</style> 