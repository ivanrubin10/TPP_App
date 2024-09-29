<template>
    <!-- Image that opens the modal -->
    <img :src="imageSrc" alt="thumbnail" @click="openModal" class="thumbnail" />
    <!-- Modal -->
    <div v-if="isModalOpen" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
            <img :src="imageSrc" alt="large image" class="large-image" />
            <button @click="closeModal" class="close-button">x</button>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'

// Props to pass the image source
const props = defineProps({
    imageSrc: {
        type: String,
        required: true
    }
})

// Reactive state for modal visibility
const isModalOpen = ref(false)

// Methods to open and close the modal
const openModal = () => {
    isModalOpen.value = true
}

const closeModal = () => {
    isModalOpen.value = false
}
</script>

<style scoped>
.image-wrapper img {
    height: auto;
    width: 100%;
    margin: 30px;
}

.thumbnail {
    width: 100%;
    padding: 30px;
    padding-top: 15px;
    cursor: pointer;
    transition: transform 0.2s;
}

.thumbnail:hover {
    transform: scale(1.02);
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background: transparent;
    backdrop-filter: blur(100px);
    border: var(--text-200) 2px solid;
    padding: 50px;
    border-radius: 8px;
    max-width: 70%;
    max-height: 70%;
    text-align: center;
    position: relative;
}

.large-image {
    max-width: 100%;
    max-height: 80vh;
}

.close-button {
    position: absolute;
    top: 8px;
    right: 12px;
    background: transparent;
    color: var(--text-100);
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
}
</style>