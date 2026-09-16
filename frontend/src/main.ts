import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";
import { createApp } from "vue";

import App from "@/App.vue";
import { primevueOptions } from "@/assets/primevue";
import { router } from "@/router";
import "@/assets/main.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(PrimeVue, primevueOptions);
app.directive("tooltip", Tooltip);
app.mount("#app");
