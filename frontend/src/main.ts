import { createPinia } from "pinia";
import { createApp } from "vue";
import { createGtag } from "vue-gtag";

import App from "@/App.vue";
import { vTooltip } from "@/directives/tooltip";
import { router } from "@/router";
import "@/assets/main.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.directive("tooltip", vTooltip);

if (import.meta.env.PROD) {
  app.use(createGtag({ tagId: "G-TZ6E25RS0Q", pageTracker: { router } }));
}

app.mount("#app");
