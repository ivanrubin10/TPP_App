<template>
    <div class="inspection-card" :style="style">
        <p>{{ title }}</p>
        <slot />
    </div>
</template>

<script setup>
defineProps({
    title: {
        type: String,
        required: true
    },
    style: {
        type: String,
        default: ''
    }
});
</script>

<style scoped>
.inspection-card {
    aspect-ratio: 1/1;
    width: clamp(100px, 31vw, 575px);
    margin: 20px;
    background-color: var(--bg-200);
    border: var(--text-200) 2px solid;
    padding: 20px;
    border-radius: 20px;
    display: flex;
    flex-direction: column;
}
.inspection-card p {
    font-weight: bold;
    text-align: center;
    font-size: 110%;
}
</style>