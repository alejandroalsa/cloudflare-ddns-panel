import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./lib/theme"; // aplica el tema guardado antes de montar, evita parpadeo
import "./style.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
