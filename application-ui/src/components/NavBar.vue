<script setup lang="ts">
</script>

<template>
  <div class="nav-bar">
    <div class="title">
      <h2>Sistema de visión</h2>
    </div>
    <ul>
      <li><router-link to="/">Inspección</router-link></li>
      <li><router-link to="/dashboard">Dashbard</router-link></li>
      <li><router-link to="/historial">Historial</router-link></li>
      <li><router-link to="/config">Configuración</router-link></li>
    </ul>
  </div>
</template>

<style scoped>
.nav-bar {
  background-color: var(--bg-100);
  display: flex;
  border-bottom: var(--accent-200) 1px solid;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  font-size: 30px;
  display: flex;
  align-items: center;
}

.title {
  width: 500px;
  margin-left: 70px;
  color: var(--text-100);
}

ul { 
  list-style-type: none;
  margin: 0;
  padding: 0 10em;
  width: 100%;
  overflow: hidden;
  display: flex;
}

li {
  float: left;
  background-color: var(--bg-100);
  padding: 20px;
  text-decoration: none;
}
li a {
  color: var(--text-100);
}
li:hover {
  background-color: var(--bg-300);
}
</style>
