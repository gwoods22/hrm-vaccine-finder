<template>
  <div id="app">
    <Appts />
  </div>
</template>

<script>
import Appts from './components/Appts.vue'

export default {
  name: 'App',
  components: {
    Appts
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
