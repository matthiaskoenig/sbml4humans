import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

// Exercise the GPU viewer in the regular CI suite as well as the focused network suite.
test.use({
  launchOptions: {
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
  },
});

const report = JSON.parse(
  readFileSync(new URL("../fixtures/repressilator.json", import.meta.url), "utf8"),
);
const validation = JSON.parse(
  readFileSync(new URL("../fixtures/validation-repressilator.json", import.meta.url), "utf8"),
);
const model = Object.values(report.reports)[0] as {
  report: { models: { pk: string; listOfSpecies: { pk: string; id: string }[] }[] };
};
const species = model.report.models[0]!.listOfSpecies[0]!;

test("complete graph includes the SBML document and every model definition", async ({ page }) => {
  const response = JSON.parse(
    readFileSync(new URL("../fixtures/model_definitions.json", import.meta.url), "utf8"),
  );
  await page.route("**/api/examples/model_definitions", (route) =>
    route.fulfill({ json: response }),
  );
  await page.goto("/examples/model_definitions?view=network&network=all");
  await page.getByTestId("network-objects-toggle").click();
  await page.getByTestId("network-search").fill("SBMLDocument");
  await expect(page.getByTestId("network-object")).toHaveCount(1);
  await page.getByTestId("network-search").fill("Model");
  await expect(page.getByTestId("network-object").filter({ hasText: "m1" })).toBeVisible();
});

test.beforeEach(async ({ page }) => {
  await page.route("**/api/validation/**", (route) => route.fulfill({ json: validation }));
  await page.route("**/api/examples/**", async (route) => {
    if (route.request().url().includes("validation")) return route.fulfill({ json: validation });
    return route.fulfill({ json: report });
  });
  await page.route(/\/api\/annotation_resource\?/, (route) => {
    const resource = new URL(route.request().url()).searchParams.get("resource")!;
    return route.fulfill({
      json: {
        resource,
        collection: resource.includes("SBO:")
          ? { prefix: "sbo" }
          : resource.includes("uniprot/")
            ? { prefix: "uniprot" }
            : null,
        ontology: resource.includes("SBO:")
          ? { ontology: "sbo", label: "polypeptide chain" }
          : null,
        uniprot: resource.includes("uniprot/P03023") ? { name: "Lactose operon repressor" } : null,
        errors: [],
        warnings: [],
      },
    });
  });
});

test("renders Cosmos and shares selection with the existing inspector and tables", async ({
  page,
}) => {
  const failures: string[] = [];
  page.on("pageerror", (error) => failures.push(error.message));
  let reports = 0;
  page.on("request", (request) => {
    if (/\/api\/examples\/BIOMD0000000012$/.test(request.url())) reports++;
  });
  await page.goto("/examples/BIOMD0000000012?view=network");
  await expect(page.getByTestId("network-view")).toBeVisible();
  await expect(page.getByTestId("network-counts")).toHaveText("18 objects · 18 links");
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30_000 });
  await expect(page.getByTestId("network-canvas").locator("canvas")).toBeVisible();
  await page.screenshot({ path: "test-results/network-light.png" });
  await page.getByTestId("network-objects-toggle").click();
  await page.getByTestId("network-search").fill(species.id);
  await page.getByTestId("network-object").filter({ hasText: species.id }).first().click();
  await expect.poll(() => new URL(page.url()).searchParams.get("pk")).toBe(species.pk);
  await expect(page.getByTestId("inspector")).toContainText(species.id);
  await page.getByTestId("inspector-close").click();
  await expect(page.getByTestId("inspector")).toHaveCount(0);
  const canvas = await page.getByTestId("network-canvas").boundingBox();
  await page.mouse.move(canvas!.x + canvas!.width / 2, canvas!.y + canvas!.height / 2);
  // Picking reads a GPU frame after the pointer moves and the inspector resizes the canvas.
  await page.evaluate(
    "new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))",
  );
  await page.getByTestId("network-canvas").screenshot({ path: "test-results/network-picking.png" });
  await page.mouse.click(canvas!.x + canvas!.width / 2, canvas!.y + canvas!.height / 2);
  await expect(page.getByTestId("inspector")).toContainText(species.id);
  await page.getByTestId("view-tables").click();
  await expect(page.getByTestId("inspector")).toContainText(species.id);
  await page.getByTestId("view-network").click();
  await expect(page.getByTestId("network-view")).toBeVisible();
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30_000 });
  expect(new URL(page.url()).searchParams.get("pk")).toBe(species.pk);
  expect(reports).toBe(1);
  expect(failures).toEqual([]);
});

test("changes projections and styles without losing selection", async ({ page }) => {
  await page.goto(`/examples/BIOMD0000000012?view=network&pk=${encodeURIComponent(species.pk)}`);
  await expect(page.getByTestId("network-view")).toBeVisible();
  await page.getByTestId("network-kind").selectOption("kinetic");
  await expect(page.getByTestId("network-counts")).not.toHaveText("18 objects · 18 links");
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30_000 });
  await page.getByRole("combobox", { name: "network style", exact: true }).selectOption("dark");
  await expect(page.getByTestId("network-canvas")).toHaveCSS("background-color", "rgb(23, 33, 43)");
  await page.getByTestId("network-labels").uncheck();
  await expect(page.getByTestId("inspector")).toContainText(species.id);
  expect(new URL(page.url()).searchParams.get("pk")).toBe(species.pk);
  await page.getByTestId("view-tables").click();
  await page.getByTestId("view-network").click();
  await expect(page.getByTestId("network-kind")).toHaveValue("kinetic");
  await page.getByRole("combobox", { name: "network style", exact: true }).selectOption("dark");
  await page.getByTestId("network-labels").uncheck();
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30_000 });
  await page.screenshot({ path: "test-results/network-dark.png" });
});

test("keeps inspection available when WebGL cannot start", async ({ page }) => {
  await page.addInitScript({
    content: `
    const getContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, ...args) {
      if (type === "webgl2") return null;
      return Reflect.apply(getContext, this, [type, ...args]);
    };
  `,
  });
  await page.goto("/examples/BIOMD0000000012?view=network");
  await expect(page.getByTestId("network-status")).toContainText("Network drawing unavailable", {
    timeout: 30_000,
  });
  await page.getByTestId("network-search").fill(species.id);
  await page.getByTestId("network-object").first().click();
  await expect(page.getByTestId("inspector")).toContainText(species.id);
});

test("resolved graph labels share the report annotation cache", async ({ page }) => {
  let requests = 0;
  page.on("request", (request) => {
    if (
      request.url().includes("/annotation_resource?") &&
      new URL(request.url()).searchParams.get("resource")?.includes("uniprot/P03023")
    )
      requests++;
  });
  await page.goto("/examples/BIOMD0000000012?view=network");
  await page.getByTestId("network-objects-toggle").click();
  await page.getByTestId("network-search").fill("PX");
  await page.getByTestId("network-object").first().click();
  await expect(page.getByTestId("inspector")).toContainText("Lactose operon repressor");
  await page.getByTestId("network-label-source").selectOption("annotation");
  await expect(
    page
      .getByTestId("viewer-labels")
      .locator("text")
      .filter({ hasText: "Lactose operon repressor" }),
  ).toBeVisible();
  await page.getByTestId("view-tables").click();
  await expect(page.getByTestId("inspector")).toContainText("Lactose operon repressor");
  await page.getByTestId("view-network").click();
  await page.getByTestId("network-label-source").selectOption("annotation");
  await expect(
    page
      .getByTestId("viewer-labels")
      .locator("text")
      .filter({ hasText: "Lactose operon repressor" }),
  ).toBeVisible();
  expect(requests).toBe(1);
  await page.getByTestId("network-objects-toggle").click();
  await page.getByTestId("network-fit").click();
  await expect(
    page
      .getByTestId("viewer-labels")
      .locator("text")
      .filter({ hasText: "Lactose operon repressor" }),
  ).toBeVisible();
  await page.screenshot({ path: "test-results/network-metadata.png" });
});

test("complete graph opens archive boundary objects in their own report entry", async ({
  page,
}) => {
  const response = JSON.parse(
    readFileSync(new URL("../fixtures/comp_models.json", import.meta.url), "utf8"),
  );
  const entries = Object.entries(response.reports) as [
    string,
    {
      report: { linkGraph: { edges: { source: string; target: string; targetEntry?: string }[] } };
    },
  ][];
  const source = entries.find(([location, value]) =>
    value.report.linkGraph.edges.some((edge) => edge.targetEntry && edge.targetEntry !== location),
  )!;
  const edge = source[1].report.linkGraph.edges.find(
    (edge) => edge.targetEntry && edge.targetEntry !== source[0],
  )!;
  await page.route("**/api/examples/comp_models", (route) => route.fulfill({ json: response }));
  await page.goto(
    `/examples/comp_models?view=network&network=all&entry=${encodeURIComponent(source[0])}`,
  );
  await page.getByTestId("network-objects-toggle").click();
  const target = page.locator(
    `[data-testid="network-object"][data-pk=${JSON.stringify(edge.target)}][data-entry=${JSON.stringify(edge.targetEntry)}]`,
  );
  await expect(target).toBeVisible();
  await target.click();
  await expect.poll(() => new URL(page.url()).searchParams.get("entry")).toBe(edge.targetEntry);
  await expect.poll(() => new URL(page.url()).searchParams.get("pk")).toBe(edge.target);
  await expect(page.getByTestId("inspector")).toBeVisible();
});

test("offers biological force layout and updates spacing without changing the graph", async ({
  page,
}) => {
  await page.goto("/examples/BIOMD0000000012?view=network&network=all");
  await expect(page.getByTestId("network-counts")).toHaveText("79 objects · 162 links");
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30000 });
  const counts = await page.getByTestId("network-counts").textContent();
  await page.getByTestId("network-layout").selectOption("force");
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30000 });
  await expect(page.getByTestId("network-counts")).toHaveText(counts!);
  await page.getByTestId("network-layout").selectOption("biological");
  await page.getByRole("combobox", { name: "network spacing", exact: true }).selectOption("1.4");
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30000 });
  await expect(page.getByTestId("viewer-labels").locator("text").first()).toBeVisible();
  await page.screenshot({ path: "test-results/network-complete.png" });
});

test("clears old GPU objects when switching to an empty model and can switch back", async ({
  page,
}) => {
  const response = JSON.parse(
    readFileSync(new URL("../fixtures/fan_out.json", import.meta.url), "utf8"),
  );
  await page.route("**/api/examples/fan_out", (route) => route.fulfill({ json: response }));
  await page.goto("/examples/fan_out?view=network&network=kinetic");
  await expect(page.getByTestId("network-canvas").locator("canvas")).toBeVisible();
  await page.getByTestId("model-select").selectOption("d0");
  await expect(page.getByTestId("network-empty")).toBeVisible();
  await expect(page.getByTestId("network-canvas").locator("canvas")).not.toBeVisible();
  await page.getByTestId("model-select").selectOption("m");
  await expect(page.getByTestId("network-empty")).toHaveCount(0);
  await expect(page.getByTestId("network-status")).toHaveCount(0, { timeout: 30000 });
  await expect(page.getByTestId("network-canvas").locator("canvas")).toBeVisible();
});
