import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AppFooter from "@/components/layout/AppFooter.vue";
import { DOCS_URL } from "@/report/glossary";

// the version and the commit are injected at build time, the tests set them instead
const build = vi.hoisted(() => ({ APP_VERSION: "1.2.3", APP_COMMIT: "" }));
vi.mock("@/build", () => build);

const COMMIT = "0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c";

describe("AppFooter", () => {
  beforeEach(() => {
    build.APP_VERSION = "1.2.3";
    build.APP_COMMIT = COMMIT;
  });

  it("names the version and links the commit the build was made from", () => {
    const wrapper = mount(AppFooter);
    expect(wrapper.get("[data-testid=app-footer]").text()).toContain("SBML4Humans 1.2.3");
    const commit = wrapper.get("[data-testid=footer-commit]");
    expect(commit.text()).toBe("0f1e2d3");
    expect(commit.attributes("href")).toBe(
      `https://github.com/matthiaskoenig/sbml4humans/commit/${COMMIT}`,
    );
  });

  it("shows the version alone when the build knows no commit", () => {
    build.APP_COMMIT = "";
    const wrapper = mount(AppFooter);
    expect(wrapper.get("[data-testid=app-footer]").text()).toContain("SBML4Humans 1.2.3");
    expect(wrapper.find("[data-testid=footer-commit]").exists()).toBe(false);
  });

  it("cites the concept DOI and the citation of the documentation", () => {
    const wrapper = mount(AppFooter);
    expect(wrapper.get("[data-testid=footer-doi]").attributes("href")).toBe(
      "https://doi.org/10.5281/zenodo.22827237",
    );
    expect(wrapper.get("[data-testid=footer-cite]").attributes("href")).toBe(
      `${DOCS_URL}#how-to-cite`,
    );
  });

  it("links the repository, the documentation, the lab and the privacy notice", () => {
    const wrapper = mount(AppFooter);
    expect(wrapper.get("[data-testid=footer-github]").attributes("href")).toBe(
      "https://github.com/matthiaskoenig/sbml4humans",
    );
    expect(wrapper.get("[data-testid=footer-docs]").attributes("href")).toBe(DOCS_URL);
    expect(wrapper.get("[data-testid=footer-lab]").attributes("href")).toBe(
      "https://livermetabolism.com",
    );
    expect(wrapper.get("[data-testid=footer-privacy]").attributes("href")).toContain(
      "privacy_notice.md",
    );
    expect(wrapper.get("[data-testid=app-footer]").text()).toContain("© 2021-2026 Matthias König");
  });
});
