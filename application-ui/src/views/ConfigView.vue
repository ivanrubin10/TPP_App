<template>
  <div class="config-page">
    <h1>Configuración</h1>
    
    <div class="config-section">
      <h2>Fuente de imagen</h2>
      <p class="section-description">Seleccione la fuente de imagen para la detección</p>
      <ImageSourceSelector v-model="imageSource" @update:modelValue="updateImageSource" />
    </div>
    
    <div class="config-section">
      <h2>Conexión</h2>
      <p class="section-description">Configuración de la conexión PLC/GALC</p>
      <div class="connection-type">
        <label>Tipo de conexión:</label>
        <select v-model="connectionType" @change="updateConnectionType">
          <option value="PLC">PLC</option>
          <option value="GALC">GALC</option>
        </select>
      </div>
      
      <div class="connection-details" v-if="connectionType === 'PLC'">
        <div class="input-group">
          <label>Host PLC:</label>
          <input type="text" v-model="plcHost" @blur="updateConfig">
        </div>
        <div class="input-group">
          <label>Puerto PLC:</label>
          <input type="number" v-model.number="plcPort" @blur="updateConfig">
        </div>
      </div>
      
      <div class="connection-details" v-if="connectionType === 'GALC'">
        <div class="input-group">
          <label>Host GALC:</label>
          <input type="text" v-model="galcHost" @blur="updateConfig">
        </div>
        <div class="input-group">
          <label>Puerto GALC:</label>
          <input type="number" v-model.number="galcPort" @blur="updateConfig">
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <h2>Detección</h2>
      <p class="section-description">Configuración de parámetros de detección</p>
      <div class="input-group">
        <label>Umbral de confianza mínima:</label>
        <input 
          type="range" 
          v-model.number="minConfThreshold" 
          min="0.1" 
          max="0.9" 
          step="0.05"
          @change="updateConfig"
        >
        <span>{{ (minConfThreshold * 100).toFixed(0) }}%</span>
      </div>
    </div>
    
    <div v-if="saveMessage" class="save-message" :class="{ error: saveError }">
      {{ saveMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useBackendApi } from '../composables/useBackendApi';
import ImageSourceSelector from '../components/ImageSourceSelector.vue';

const { getConfig, saveConfig } = useBackendApi();

// Configuration state
const imageSource = ref('camera');
const connectionType = ref('PLC');
const plcHost = ref('127.0.0.1');
const plcPort = ref(12345);
const galcHost = ref('127.0.0.1');
const galcPort = ref(54321);
const minConfThreshold = ref(0.7);

// UI state
const saveMessage = ref('');
const saveError = ref(false);

// Load configuration on mount
onMounted(async () => {
  await loadConfig();
});

// Load configuration from backend
const loadConfig = async () => {
  try {
    const config = await getConfig();
    console.log('Loaded configuration:', config);
    
    // Update local state with loaded config
    imageSource.value = config.image_source || 'camera';
    connectionType.value = config.connection_type || 'PLC';
    plcHost.value = config.plc_host || '127.0.0.1';
    plcPort.value = config.plc_port || 12345;
    galcHost.value = config.galc_host || '127.0.0.1';
    galcPort.value = config.galc_port || 54321;
    minConfThreshold.value = config.min_conf_threshold || 0.7;
  } catch (error) {
    console.error('Error loading configuration:', error);
    showMessage('Error al cargar la configuración', true);
  }
};

// Update image source
const updateImageSource = async (newSource) => {
  try {
    imageSource.value = newSource;
    await updateConfig();
  } catch (error) {
    console.error('Error updating image source:', error);
    showMessage('Error al actualizar la fuente de imagen', true);
  }
};

// Update connection type
const updateConnectionType = async () => {
  try {
    await updateConfig();
  } catch (error) {
    console.error('Error updating connection type:', error);
    showMessage('Error al actualizar el tipo de conexión', true);
  }
};

// Update configuration
const updateConfig = async () => {
  try {
    const configData = {
      image_source: imageSource.value,
      connection_type: connectionType.value,
      plc_host: plcHost.value,
      plc_port: plcPort.value,
      galc_host: galcHost.value,
      galc_port: galcPort.value,
      min_conf_threshold: minConfThreshold.value
    };
    
    await saveConfig(configData);
    showMessage('Configuración guardada correctamente');
  } catch (error) {
    console.error('Error saving configuration:', error);
    showMessage('Error al guardar la configuración', true);
  }
};

// Show message with auto-hide
const showMessage = (message, isError = false) => {
  saveMessage.value = message;
  saveError.value = isError;
  
  setTimeout(() => {
    saveMessage.value = '';
  }, 3000);
};
</script>

<style scoped>
.config-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  color: var(--text-100);
}

h1 {
  font-size: 2rem;
  margin-bottom: 30px;
  color: var(--text-100);
}

h2 {
  font-size: 1.5rem;
  margin-bottom: 10px;
  color: var(--text-100);
}

.config-section {
  background-color: var(--bg-300);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 30px;
}

.section-description {
  color: var(--text-200);
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.input-group label {
  width: 200px;
  margin-right: 10px;
}

.input-group input, .input-group select {
  flex: 1;
  padding: 8px;
  border-radius: 5px;
  border: 1px solid var(--bg-200);
  background-color: var(--bg-100);
  color: var(--text-100);
}

.input-group input[type="range"] {
  flex: 1;
  margin-right: 10px;
}

.connection-type {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.connection-type label {
  width: 200px;
  margin-right: 10px;
}

.connection-type select {
  flex: 1;
  padding: 8px;
  border-radius: 5px;
  border: 1px solid var(--bg-200);
  background-color: var(--bg-100);
  color: var(--text-100);
}

.connection-details {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--bg-200);
}

.save-message {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  border-radius: 5px;
  background-color: var(--good-100);
  color: var(--bg-300);
  font-weight: bold;
  z-index: 1000;
}

.save-message.error {
  background-color: var(--no-good-100);
}
</style>
