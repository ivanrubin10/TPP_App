<template>
    <button class="btn btn-danger" @click="onClick()">{{ text }}</button>
</template>

<script lang="ts" setup>
// define props for onclick and button content
defineProps({
    onClick: {
        type: Function,
        required: true
    },
    text: {
        type: String,
        required: true
    }
});
</script>

<style scoped>
button {
    height: 90px;
    width: 180px;
    border-radius: 15px;
    background-color: var(--primary-100);
    color: var(--text-200);
    border: var(--text-200) 2px solid;
    font-size: 16pt;
    cursor: pointer;
}
</style>