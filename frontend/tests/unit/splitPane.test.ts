import { mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { nextTick } from "vue";

import SplitPane from "@/components/layout/SplitPane.vue";

const KEY = "sbml4humans.split.test";

const measure = Element.prototype.getBoundingClientRect;

/** jsdom measures every box as empty, so the size of the container is stated for the tests which
 * need one. */
function measureAs(width: number, height: number): void {
  Element.prototype.getBoundingClientRect = () =>
    ({ width, height, top: 0, left: 0, right: width, bottom: height, x: 0, y: 0 }) as DOMRect;
}

function mountPane(direction: "horizontal" | "vertical", sizedPane: "first" | "second" = "first") {
  return mount(SplitPane, {
    props: { direction, storageKey: "test", initial: 240, min: 160, sizedPane },
  });
}

describe("SplitPane", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    Element.prototype.getBoundingClientRect = measure;
  });

  it("keeps a size stored on a wider window inside the container", async () => {
    // the reader dragged the pane to 900 px on a wide screen and opens the page on a narrow one
    localStorage.setItem(KEY, "900");
    measureAs(600, 400);
    const handle = mountPane("horizontal", "second").get("[data-testid=split-handle]");
    await nextTick();
    // the other pane keeps its minimum, and the stored size survives for the wide screen
    expect(handle.attributes("aria-valuenow")).toBe("440");
    expect(localStorage.getItem(KEY)).toBe("900");
  });

  it("gives the window resize the size back which fits again", async () => {
    localStorage.setItem(KEY, "900");
    measureAs(600, 400);
    const handle = mountPane("horizontal", "second").get("[data-testid=split-handle]");
    await nextTick();
    expect(handle.attributes("aria-valuenow")).toBe("440");
    measureAs(1600, 400);
    window.dispatchEvent(new Event("resize"));
    await nextTick();
    expect(handle.attributes("aria-valuenow")).toBe("900");
  });

  it("describes the separator of a horizontal split for assistive technology", () => {
    const handle = mountPane("horizontal").get("[data-testid=split-handle]");
    expect(handle.attributes("role")).toBe("separator");
    expect(handle.attributes("tabindex")).toBe("0");
    expect(handle.attributes("aria-orientation")).toBe("vertical");
    expect(handle.attributes("aria-valuenow")).toBe("240");
  });

  it("resizes with the arrow keys along the split and remembers the size", async () => {
    const handle = mountPane("horizontal").get("[data-testid=split-handle]");
    await handle.trigger("keydown", { key: "ArrowRight" });
    expect(localStorage.getItem(KEY)).toBe("256");
    expect(handle.attributes("aria-valuenow")).toBe("256");
    await handle.trigger("keydown", { key: "ArrowLeft" });
    expect(localStorage.getItem(KEY)).toBe("240");
    await handle.trigger("keydown", { key: "ArrowUp" });
    expect(localStorage.getItem(KEY)).toBe("240");
  });

  it("grows the sized second pane upwards and keeps the minimum", async () => {
    const handle = mountPane("vertical", "second").get("[data-testid=split-handle]");
    expect(handle.attributes("aria-orientation")).toBe("horizontal");
    await handle.trigger("keydown", { key: "ArrowUp" });
    expect(localStorage.getItem(KEY)).toBe("256");
    for (let step = 0; step < 20; step += 1) {
      await handle.trigger("keydown", { key: "ArrowDown" });
    }
    expect(localStorage.getItem(KEY)).toBe("160");
  });
});
