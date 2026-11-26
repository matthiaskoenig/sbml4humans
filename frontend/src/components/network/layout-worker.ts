import { computeLayout, type LayoutOptions } from "@graphvis/viewer/layout";

self.onmessage = (
  event: MessageEvent<{ count: number; links: Float32Array; options: LayoutOptions }>,
) => {
  const positions = computeLayout(event.data.count, event.data.links, event.data.options);
  self.postMessage(positions, { transfer: [positions.buffer] });
};
