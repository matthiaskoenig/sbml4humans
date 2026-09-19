import { createPinia } from "pinia";
import { createApp } from "vue";
import { createGtag } from "vue-gtag";

import { analyticsEnabled, gtagSettings } from "@/analytics";
import App from "@/App.vue";
import { vTooltip } from "@/directives/tooltip";
import { router } from "@/router";
import "@/assets/main.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.directive("tooltip", vTooltip);

if (analyticsEnabled(import.meta.env)) {
  app.use(createGtag(gtagSettings(router)));
}

app.mount("#app");
