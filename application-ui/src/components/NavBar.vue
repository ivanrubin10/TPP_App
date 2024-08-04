<script setup lang="ts">
</script>

<template>
  <div class="nav-bar">
    <div class="title">
      <h2>Sistema de visión</h2>
    </div>
    <ul>
      <li><router-link to="/">Inspección</router-link></li>
      <li><router-link to="/dashboard">Dashboard</router-link></li>
      <li><router-link to="/historial">Historial</router-link></li>
      <li><router-link to="/config">Configuración</router-link></li>
    </ul>
  </div>
</template>

<style scoped>
.nav-bar {
  background-color: var(--bg-100);
  position: fixed;
  border-bottom: var(--accent-200) 1px solid;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  padding: 0 70px;
  font-size: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  width: 500px;
  color: var(--text-100);
}

ul { 
  list-style-type: none;
  margin: 0;
  padding-left: 0;
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

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}
</style>
