<template>
    <div class="footer-container" ref="scrollableContainer" @mousedown="handleMouseDown" @wheel="handleWheel">
        <div class="footer-content" ref="footerContent">
            <div class="footer-item" v-for="(item, index) in items" :key="index" :style="getItemStyle(index)"
                @click="setSelectedItem(index)">
                <div class="footer-item-content">
                    <div class="footer-item-header">
                        <span class="footer-item-header-name">{{ item.name }}</span>
                    </div>
                    <div class="footer-item-body">
                        <span class="footer-item-body-info">{{ item.info }}</span>
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
import { ref, onMounted, onUnmounted, defineEmits } from "vue";

const props = defineProps({
    items: {
        type: Array as () => Array<{ id: string, name: string, info: string, date: string, outcome: string }>,
        required: true
    },
    modelValue: {
        type: Object,
    }
})

const emit = defineEmits(['update:modelValue']);

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
    const walk = (x - startX); // scroll-fast
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

onMounted(() => {
    document.addEventListener('mouseup', handleMouseUp);
});

onUnmounted(() => {
    document.removeEventListener('mouseup', handleMouseUp);
});

function setSelectedItem(index: number) {
    //sets the is-selected class to the selected item
    const itemsElements = document.querySelectorAll('.footer-item');
    itemsElements.forEach((item) => {
        item.classList.remove('is-selected');
    });
    itemsElements[index].classList.add('is-selected');
    emit('update:modelValue', items.value[index]);
}
const getItemStyle = (index: number) => {
    if (items.value[index].outcome === 'success') {
        return { backgroundImage: 'linear-gradient(180deg, var(--good-100) 0%, var(--good-100) 100%)' };
    } else if (items.value[index].outcome === 'failure') {
        // Other items style (grayed out)
        return { backgroundImage: 'linear-gradient(180deg, var(--no-good-100) 0%, var(--no-good-100) 100%)' };
    }
    // Other items style (grayed out)
    return { backgroundColor: 'var(--bg-300)' };
};
</script>

<style scoped>
.footer-container {
    width: 100%;
    background-color: var(--bg-100);
    position: fixed;
    padding: 0 55px;
    bottom: 0;
    overflow-x: hidden;
    overflow-y: hidden;
    white-space: nowrap;
    border-top: var(--accent-200) 1px solid;
    height: 220px;
    /* Set a fixed height to ensure consistent height */
    display: flex;
    cursor: pointer;
    /* To ensure it expands to the content */
    align-items: center;
    /* Center content vertically if needed */
    z-index: 1000;
    /* Ensure it stays on top of other content */
}

.footer-content {
    display: flex;
}

.footer-item {
    width: 280px;
    height: 170px; /* Adjust to fit content */
    background-color: var(--good-green);
    color: var(--text-100);
    margin: 15px;
    border-radius: 5px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: flex-start;
    padding: 10px;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
    position: relative;
    font-family: sans-serif;
}

.footer-item-content {
    display: flex;
    flex-direction: column;
    width: 100%;
}

.footer-item-header {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
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
    font-size: 0.9em;
    min-width: 200px;
    height: 35px;
    white-space: wrap;
    margin-bottom: 15px;
}

.footer-item-body-info {
    display: block;
}

.footer-footer {
  display: flex;
  justify-content: space-between;  
  width: 100%;
  position: relative;
  bottom: -5px;
  margin-top: 10px;
}
.footer-item-image {
    width: 100px;
    height: auto;
    margin: 0 auto;
    filter: invert(0.8);
}

.footer-item-body-date {
    font-size: 0.8em;
}

.is-selected {
    border: var(--accent-200) 2px solid;
    transform: scale(1.1);
}
</style>
