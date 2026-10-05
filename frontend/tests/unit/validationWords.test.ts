import { describe, expect, it } from "vitest";

import type { EntrySkip } from "@/report/validationIndex";
import { skipWords } from "@/report/validationWords";

const REASONS: EntrySkip[] = ["expandedSize", "timeout", "memory", "crashed", "busy", "unanswered"];

describe("skipWords", () => {
  it("says why for every reason, briefly and at length, each in its own words", () => {
    const shorts = new Set<string>();
    const longs = new Set<string>();
    for (const reason of REASONS) {
      const words = skipWords(reason, true);
      expect(words.short).toMatch(/^libsbml did not check this document: /);
      expect(words.long).toMatch(/^libsbml did not check this document: /);
      expect(words.long.length).toBeGreaterThan(words.short.length);
      shorts.add(words.short);
      longs.add(words.long);
    }
    expect(shorts.size).toBe(REASONS.length);
    expect(longs.size).toBe(REASONS.length);
  });

  it("says that the check of a crashed document ended abnormally", () => {
    expect(skipWords("crashed", true).short).toContain("ended abnormally");
    expect(skipWords("crashed", true).long).toContain("ended abnormally");
  });

  it("asks to reload a busy report, and to load a file or pasted content again", () => {
    expect(skipWords("busy", true).short).toContain("reload the report later");
    expect(skipWords("busy", true).long).toContain("Reload the report later");
    for (const words of Object.values(skipWords("busy", false))) {
      expect(words).toMatch(/load it again later/i);
      expect(words).not.toMatch(/reload/i);
    }
  });

  it("keeps the words of every other reason independent of a reload", () => {
    for (const reason of REASONS.filter((r) => r !== "busy")) {
      expect(skipWords(reason, false)).toEqual(skipWords(reason, true));
    }
  });
});
