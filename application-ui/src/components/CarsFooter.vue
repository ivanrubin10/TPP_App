<template>
    <div class="footer-container" ref="scrollableContainer" @mousedown="handleMouseDown" @wheel="handleWheel">
        <div class="footer-content" ref="footerContent">
            <div 
                v-for="(item, index) in items" 
                :key="item.id" 
                :class="['footer-item', {'is-selected': isItemSelected(item)}]"
                :style="getItemStyle(index)"
                @click="handleItemClick(index)"
                :id="`footer-item-${item.id}`"
            >
                <div class="footer-item-content">
                    <div class="footer-item-header">
                        <span class="footer-item-header-name">Esperado: {{ item.expectedPart }}</span>
                        <span v-if="item.isQueued" class="queued-badge">En cola</span>
                    </div>
                    <img class="footer-item-image" src="@/assets/Car-2-icon.png" alt="Car Image">
                    <div class="footer-footer">
                        <span class="footer-item-header-id">{{ item.id }}</span>
                        <span class="footer-item-body-date">{{ formatDate(item.date) }}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';

const props = defineProps({
    items: {
        type: Array as () => Array<{ 
            id: string, 
            expectedPart: string, 
            actualPart: string, 
            outcome: string,  
            date: string,
            isQueued: boolean 
        }>,
        required: true
    },
    modelValue: {
        type: Object,
        default: null
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

function isItemSelected(item: any) {
    return props.modelValue && props.modelValue.id === item.id;
}

function handleItemClick(index: number) {
    const clickedItem = items.value[index];
    console.log('Footer item clicked:', clickedItem);
    emit('item-clicked', clickedItem);
}

function getItemStyle(index: number) {
    const item = items.value[index];
    if (item.isQueued) {
        return { backgroundImage: 'linear-gradient(180deg, var(--bg-300) 0%, var(--bg-400) 100%)' };
    } else if (item.outcome === 'GOOD') {
        return { backgroundImage: 'linear-gradient(180deg, var(--good-100) 0%, var(--good-100) 100%)' };
    } else if (item.outcome === 'NOGOOD') {
        return { backgroundImage: 'linear-gradient(180deg, var(--no-good-100) 0%, var(--no-good-100) 100%)' };
    }
    return { backgroundColor: 'var(--bg-300)' };
}

// Method to programmatically highlight a car in the footer and scroll to it
function highlightItem(itemId: string) {
    if (!itemId) return;
    
    // Wait for next DOM update
    nextTick(() => {
        // Find the item in the DOM
        const itemElement = document.getElementById(`footer-item-${itemId}`);
        if (itemElement) {
            // Scroll the item into view
            itemElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        } else {
            console.warn(`Could not find DOM element for item ${itemId}`);
        }
    });
}

// Watch for changes to the modelValue and highlight the selected item
watch(() => props.modelValue, (newValue) => {
    if (newValue) {
        console.log('Model value changed in footer, highlighting item:', newValue.id);
        highlightItem(newValue.id);
    }
}, { deep: true });

// Watch for changes to the items array
watch(() => props.items, (newItems) => {
    items.value = newItems;
    
    // If modelValue is set, highlight the corresponding item
    if (props.modelValue) {
        nextTick(() => {
            highlightItem(props.modelValue.id);
        });
    }
}, { deep: true });

// Add date formatting function
function formatDate(dateStr: string) {
    if (!dateStr) return '';
    
    // Date is already in the format "DD-MM-YYYY HH:mm:ss"
    const [datePart, timePart] = dateStr.split(' ');
    if (!timePart) return dateStr;
    
    // Extract hours and minutes from time
    const [hours, minutes] = timePart.split(':');
    
    // Return formatted time
    return `${hours}:${minutes}`;
}

onMounted(() => {
    document.addEventListener('mouseup', handleMouseUp);
    
    // On initial mount, highlight the selected item if any
    if (props.modelValue) {
        nextTick(() => {
            highlightItem(props.modelValue.id);
        });
    }
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

.queued-badge {
    background-color: var(--accent-200);
    width: min-content;
    color: var(--bg-200);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8em;
    margin-top: 4px;
    display: inline-block;
}
</style>
