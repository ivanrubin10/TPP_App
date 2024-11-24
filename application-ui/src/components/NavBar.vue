<template>
  <div class="nav-bar">
    <div class="title">
      <h2>Sistema de visión</h2>
    </div>
    <div class="mobile-menu" @click="toggleSideMenu">
      <label class="hamb"><span class="hamb-line"></span></label>
    </div>
    <ul id="menu">
      <li :class="{ 'active': routePath === '/' }">
        <router-link to="/">Inspección</router-link>
      </li>
      <li :class="{ 'active': routePath === '/dashboard' }">
        <router-link to="/dashboard">Dashboard</router-link>
      </li>
      <li :class="{ 'active': routePath === '/historial' }">
        <router-link to="/historial">Historial</router-link>
      </li>
      <li :class="{ 'active': routePath === '/config' }">
        <router-link to="/config">Configuración</router-link>
      </li>
    </ul>

  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';

// Get the current route
const route = useRoute();
const routePath = ref(route.path);

// Watch the route path and update routePath when it changes
watch(route, () => {
  routePath.value = route.path;
});

function toggleSideMenu() {
  const sideMenu = document.getElementById('menu');
  if (sideMenu) {
    sideMenu.style.display = sideMenu.style.display === 'flex' ? 'none' : 'flex';
  }
}

</script>

<style scoped>
.nav-bar {
  background-color: var(--bg-100);
  border-bottom: var(--accent-200) 1px solid;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  height: 83px;
  padding: 0 70px;
  font-size: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  width: fit-content;
  text-wrap: nowrap;
  color: var(--text-100);
  font-size: clamp(0.7em, 2vw, 2em);
  margin-right: 50px;
}

ul {
  list-style-type: none;
  margin: 0;
  padding-left: 0;
  display: flex;
}

li {
  float: left;
  background-color: var(--bg-100);
  padding: 20px;
  text-decoration: none;
  font-size: clamp(0.7em, 2vw, 1em);
}

.active {
  background-color: var(--bg-300);
}

.active a {
  text-decoration: underline;
}

li a {
  text-decoration: none;
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

/* Menu Icon */
.hamb {
  cursor: pointer;
  float: right;
  padding: 40px 20px;
}

/* Style label tag */

.hamb-line {
  background: white;
  display: block;
  height: 2px;
  position: relative;
  width: 24px;

}

/* Style span tag */

.hamb-line::before,
.hamb-line::after {
  background: white;
  content: '';
  display: block;
  height: 100%;
  position: absolute;
  transition: all .2s ease-out;
  width: 100%;
}

.hamb-line::before {
  top: 5px;
}

.hamb-line::after {
  top: -5px;
}

.side-menu {
  display: none;
}

/* Hide checkbox */

.mobile-menu {
  display: none;
}

@media screen and (max-width: 930px) {
  .mobile-menu {
    display: block;
  }
  .nav-bar {
  }

  .nav-bar ul {
    display: none;
    position: absolute;
    flex-direction: column;
    transform: translateY(calc(100% - 88px));
    left: 0;
    background-color: var(--bg-100);
    width: 100%;
  }



}
</style>
