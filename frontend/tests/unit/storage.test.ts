import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import UrlInput from "@/components/input/UrlInput.vue";
import SplitPane from "@/components/layout/SplitPane.vue";
import { readStorage, writeStorage } from "@/storage";

describe("readStorage/writeStorage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reads back a written value", () => {
    writeStorage("storage-test-key", "value");
    expect(readStorage("storage-test-key")).toBe("value");
  });

  it("returns null and drops the write when localStorage throws", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(readStorage("storage-test-key")).toBeNull();
    expect(() => writeStorage("storage-test-key", "value")).not.toThrow();
  });
});

describe("components with a blocked localStorage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  function blockStorage(): void {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
  }

  it("still mounts UrlInput", () => {
    blockStorage();
    expect(() => mount(UrlInput)).not.toThrow();
  });

  it("still mounts SplitPane", () => {
    blockStorage();
    expect(() =>
      mount(SplitPane, {
        props: { direction: "horizontal", storageKey: "test-pane", initial: 200 },
        slots: { first: "first", second: "second" },
      }),
    ).not.toThrow();
  });
});
