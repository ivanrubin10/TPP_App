<template>
  <NavBar />
  <router-view class="container"/>
</template>

<script lang="ts" setup>
import NavBar from './components/NavBar.vue'
</script>

<style>
.container {
  height: 80vh;
  overflow-y: auto; /* Enable vertical scrolling */
  background-color: var(--bg-100);
  padding: 0 15em;
  padding-top: 50px;
  margin-top: 2em;
  color: #f5f5f5;
  font-family: sans-serif;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>