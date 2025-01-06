<template>
  <div class="config">
    <div class="config-content">
      <h1>Configuración</h1>

      <!-- Campo para el umbral -->
      <div class="umbral-input">
        <label for="umbral">Umbral (Threshold):</label>
        <input
          v-model.number="umbral"
          type="number"
          id="umbral"
          class="umbral"
          min="0.5"
          max="1.0"
        />
      </div>

      <!-- Selector de tipo de conexión -->
      <div class="connection-type">
        <label>Tipo de Conexión:</label>
        <div class="toggle-buttons">
          <button 
            :class="['toggle-btn', connectionType === 'PLC' ? 'active' : '']"
            @click="connectionType = 'PLC'"
          >
            PLC
          </button>
          <button
            :class="['toggle-btn', connectionType === 'GALC' ? 'active' : '']"
            @click="connectionType = 'GALC'"
          >
            GALC
          </button>
        </div>
      </div>

      <!-- Campos para PLC -->
      <div v-if="connectionType === 'PLC'">
        <div class="plc-input">
          <label for="plc-host">PLC Host:</label>
          <input v-model="plcHost" type="text" id="plc-host" class="plc-host" />
        </div>

        <div class="plc-input">
          <label for="plc-port">PLC Port:</label>
          <input
            v-model.number="plcPort"
            type="number"
            id="plc-port"
            class="plc-port"
            min="1"
            max="65535"
          />
        </div>
      </div>

      <!-- Campos para GALC -->
      <div v-if="connectionType === 'GALC'">
        <div class="plc-input">
          <label for="galc-host">GALC Host:</label>
          <input v-model="galcHost" type="text" id="galc-host" class="plc-host" />
        </div>

        <div class="plc-input">
          <label for="galc-port">GALC Port:</label>
          <input
            v-model.number="galcPort"
            type="number"
            id="galc-port"
            class="plc-port"
            min="1"
            max="65535"
          />
        </div>
      </div>

      <button @click="handleSave" class="save-button">Guardar</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useBackendApi } from '../composables/useBackendApi'

const { getConfig, saveConfig } = useBackendApi()

// Variables reactivas para la configuración
const umbral = ref('')
const connectionType = ref('PLC')
const plcHost = ref('')
const plcPort = ref(0)
const galcHost = ref('')
const galcPort = ref(0)

// Obtener configuración inicial al montar el componente
onMounted(() => {
  getConfig().then((config) => {
    umbral.value = config.min_conf_threshold
    connectionType.value = config.connection_type
    plcHost.value = config.plc_host
    plcPort.value = config.plc_port
    galcHost.value = config.galc_host
    galcPort.value = config.galc_port
  })
})

// Guardar la configuración en el backend
const handleSave = async () => {
  try {
    await saveConfig({
      min_conf_threshold: umbral.value,
      connection_type: connectionType.value,
      plc_host: plcHost.value,
      plc_port: plcPort.value,
      galc_host: galcHost.value,
      galc_port: galcPort.value
    })
    alert('Configuración guardada exitosamente!')
  } catch (error) {
    alert('Error al guardar la configuración.')
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

.connection-type {
  margin-bottom: 20px;
}

.toggle-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 10px;
}

.toggle-btn {
  padding: 8px 20px;
  border: 2px solid var(--text-200);
  border-radius: 4px;
  background: var(--bg-200);
  color: white;
  cursor: pointer;
}

.toggle-btn.active {
  background: var(--text-200);
  color: var(--bg-300);
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

.plc-input {
  margin-bottom: 20px;
}

.plc-host,
.plc-port {
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
