<template>
  <NavBar />
  <router-view/>
</template>

<script lang="ts" setup>
import NavBar from './components/NavBar.vue';
import socket from './composables/socket'; // Import the socket to ensure it's initialized

// Optionally, you can listen for connection events here if needed
socket.on('connect', () => {
  console.log('Socket connected');
});

socket.on('disconnect', () => {
  console.log('Socket disconnected');
});
</script>

<style>
:root {
  --bg-100: #1a1a1a;
  --bg-200: #2a2a2a;
  --bg-300: #3a3a3a;
  --text-100: #f5f5f5;
  --text-200: #e0e0e0;
  --accent-100: #4a90e2;
  --accent-200: #357abd;
  --good-100: #4caf50;
  --no-good-100: #f44336;
}

body {
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
  background-color: var(--bg-100);
  color: var(--text-100);
}
</style>