<template>
    <div class="footer-container" ref="scrollableContainer" @mousedown="handleMouseDown" @wheel="handleWheel">
        <div class="footer-content" ref="footerContent">
            <div class="footer-item" v-for="(item, index) in items" :key="index" :style="getItemStyle(index)"
                @click="handleItemClick(index)">
                <div class="footer-item-content">
                    <div class="footer-item-header">
                        <span class="footer-item-header-name">Expected: {{ item.expectedPart }}</span>
                    </div>
                    <img class="footer-item-image" src="@/assets/Car-2-icon.png" alt="Car Image">
                    <div class="footer-footer">
                        <span class="footer-item-header-id">{{ item.id }}</span>
                        <span class="footer-item-body-date">{{ item.date }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps({
    items: {
        type: Array as () => Array<{ id: string, expectedPart: string, actualPart: string, outcome: string,  date: string, }>,
        required: true
    },
    modelValue: {
        type: Object,
    }
});

const emit = defineEmits(['update:modelValue', 'item-clicked']);

const items = ref(props.items);
const scrollableContainer = ref<HTMLDivElement | null>(null);
const footerContent = ref<HTMLDivElement | null>(null);
let isDragging = false;
let startX = 0;
let scrollLeft = 0;

const handleMouseDown = (e: MouseEvent) => {
    if (!scrollableContainer.value) return;
    isDragging = true;
    startX = e.pageX - scrollableContainer.value.offsetLeft;
    scrollLeft = scrollableContainer.value.scrollLeft;
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
};

const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !scrollableContainer.value) return;
    e.preventDefault();
    const x = e.pageX - scrollableContainer.value.offsetLeft;
    const walk = (x - startX);
    scrollableContainer.value.scrollLeft = scrollLeft - walk;
};

const handleMouseUp = () => {
    isDragging = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
};

const handleWheel = (e: WheelEvent) => {
    if (!scrollableContainer.value) return;
    e.preventDefault();
    scrollableContainer.value.scrollLeft += e.deltaY;
};

function handleItemClick(index: number) {
    emit('item-clicked', items.value[index]);
    const itemsElements = document.querySelectorAll('.footer-item');
    itemsElements.forEach((item) => {
        item.classList.remove('is-selected');
    });
    itemsElements[index].classList.add('is-selected');
}

function getItemStyle(index: number) {
    if (items.value[index].outcome === 'GOOD') {
        return { backgroundImage: 'linear-gradient(180deg, var(--good-100) 0%, var(--good-100) 100%)' };
    } else if (items.value[index].outcome === 'NOGOOD') {
        return { backgroundImage: 'linear-gradient(180deg, var(--no-good-100) 0%, var(--no-good-100) 100%)' };
    }
    return { backgroundColor: 'var(--bg-300)' };
}

onMounted(() => {
    document.addEventListener('mouseup', handleMouseUp);
});

onUnmounted(() => {
    document.removeEventListener('mouseup', handleMouseUp);
});
</script>

<style scoped>
.footer-container {
    width: 100%;
    height: clamp(150px, 12vw, 250px);
    background-color: var(--bg-200);
    overflow-x: hidden;
    overflow-y: hidden;
    white-space: nowrap;
    border-top: var(--accent-200) 1px solid;
    padding: 0 55px;
    /* Set a fixed height to ensure consistent height */
    display: flex;
    cursor: pointer;
    /* To ensure it expands to the content */
    align-items: center;
    /* Center content vertically if needed */
    z-index: 10;
    /* Ensure it stays on top of other content */
}

.footer-content {
    display: flex;
}

.footer-item {
    width: 300px;
    height: clamp(100px, 10vw, 200px);
    /* Adjust to fit content */
    background-color: var(--good-green);
    color: var(--text-100);
    margin: 15px;
    border-radius: 5px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: flex-start;
    padding: 7px;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
    position: relative;
    font-family: sans-serif;
}

.footer-item-content {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    justify-content: space-between;
}

.footer-item-header {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-bottom: 5px;
    font-size: 1em;
}

.footer-item-header-id {
    font-weight: bold;
}

.footer-item-header-name {
    margin-bottom: 0;
}

.footer-item-body {
    font-size: 0.8em;
    min-width: 200px;
    height: 25px;
    white-space: wrap;
}

.footer-item-body-info {
    display: block;
}

.footer-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    position: relative;
    margin-top: 5px;
}

.footer-item-image {
    width: 7vw;
    height: auto;
    margin: 0 auto;
    filter: invert(0.8);
    -webkit-user-drag: none;
    user-select: none;
    -moz-user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
}

.footer-item-body-date {
    font-size: 0.8em;
}

.is-selected {
    border: var(--accent-200) 2px solid;
    transform: scale(1.1);
}
</style>
