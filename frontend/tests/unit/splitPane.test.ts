import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it } from "vitest";

import SplitPane from "@/components/layout/SplitPane.vue";

const KEY = "sbml4humans.split.test";

function mountPane(direction: "horizontal" | "vertical", sizedPane: "first" | "second" = "first") {
  return mount(SplitPane, {
    props: { direction, storageKey: "test", initial: 240, min: 160, sizedPane },
  });
}

describe("SplitPane", () => {
  beforeEach(() => {
    localStorage.clear();
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
