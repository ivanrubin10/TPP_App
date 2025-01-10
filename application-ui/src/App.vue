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