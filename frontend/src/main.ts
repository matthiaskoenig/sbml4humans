import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import Tooltip from "primevue/tooltip";
import { createApp } from "vue";
import { createGtag } from "vue-gtag";

import App from "@/App.vue";
import { primevueOptions } from "@/assets/primevue";
import { router } from "@/router";
import "@/assets/main.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(PrimeVue, primevueOptions);
app.directive("tooltip", Tooltip);

if (import.meta.env.PROD) {
  app.use(createGtag({ tagId: "G-TZ6E25RS0Q", pageTracker: { router } }));
}

app.mount("#app");
