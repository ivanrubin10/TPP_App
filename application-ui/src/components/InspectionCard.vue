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
        type: String
    }
});
</script>

<style scoped>
.inspection-card {
    width: 35%;
    height: 100%;
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