import { createApp } from "vue";
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";

import App from "@/App.vue";
import { primevueOptions } from "@/assets/primevue";
import "@/assets/main.css";

const app = createApp(App);
app.use(PrimeVue, primevueOptions);
app.directive("tooltip", Tooltip);
app.mount("#app");
