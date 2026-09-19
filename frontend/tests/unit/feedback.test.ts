import { beforeEach, describe, expect, it, vi } from "vitest";

import { issueUrl } from "@/feedback";

const build = vi.hoisted(() => ({ APP_VERSION: "1.2.3", APP_COMMIT: "" }));
vi.mock("@/build", () => build);

const COMMIT = "0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c";

/** The body a new issue opens with. */
function bodyOf(url: string): string {
  const parsed = new URL(url);
  expect(`${parsed.origin}${parsed.pathname}`).toBe(
    "https://github.com/matthiaskoenig/sbml4humans/issues/new",
  );
  return parsed.searchParams.get("body") ?? "";
}

describe("issueUrl", () => {
  beforeEach(() => {
    build.APP_COMMIT = COMMIT;
  });

  it("names the build, the page and the browser", () => {
    const body = bodyOf(issueUrl({ fullPath: "/examples", path: "/examples", source: null }));
    expect(body).toContain("- SBML4Humans 1.2.3 (0f1e2d3)");
    expect(body).toContain("- page: `/examples`");
    expect(body).toContain(`- browser: ${navigator.userAgent}`);
    expect(body).not.toContain("- model:");
  });

  it("names the version alone when the build knows no commit", () => {
    build.APP_COMMIT = "";
    const body = bodyOf(issueUrl({ fullPath: "/", path: "/", source: null }));
    expect(body).toContain("- SBML4Humans 1.2.3\n");
  });

  it("names an example and the view of it", () => {
    const fullPath = "/examples/repressilator?pk=m/Species:PX";
    const body = bodyOf(
      issueUrl({
        fullPath,
        path: "/examples/repressilator",
        source: { kind: "example", id: "repressilator", name: "repressilator" },
      }),
    );
    expect(body).toContain(`- page: \`${fullPath}\``);
    expect(body).toContain("- model: the example `repressilator`");
  });

  it("names the url of a model which was loaded from one", () => {
    const url = "https://example.invalid/model.xml";
    const body = bodyOf(
      issueUrl({
        fullPath: `/report?url=${encodeURIComponent(url)}`,
        path: "/report",
        source: { kind: "url", url, name: "model.xml" },
      }),
    );
    expect(body).toContain(`- model: ${url}`);
  });

  it.each(["file", "content", "local"] as const)(
    "says nothing about a model of the reader, a %s",
    (kind) => {
      const body = bodyOf(
        issueUrl({
          fullPath: "/report?pk=secret_model/Species:secret_species&local=token",
          path: "/report",
          source: { kind, name: "secret_model.xml", token: "token" },
        }),
      );
      expect(body).toContain("- page: `/report`");
      expect(body).toContain("- model: a file of my own");
      expect(body).not.toContain("secret");
      expect(body).not.toContain("token");
    },
  );
});
