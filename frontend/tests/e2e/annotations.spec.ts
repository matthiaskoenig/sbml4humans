import { expect, test } from "@playwright/test";

// a species annotated with a compound, a term and a protein
const ANNOTATED_MODEL = `<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="annotated">
    <listOfCompartments>
      <compartment id="c" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species metaid="meta_S1" id="S1" compartment="c" initialConcentration="1" hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false">
        <annotation>
          <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
            <rdf:Description rdf:about="#meta_S1">
              <bqbiol:is>
                <rdf:Bag>
                  <rdf:li rdf:resource="https://identifiers.org/CHEBI:31696"/>
                  <rdf:li rdf:resource="https://identifiers.org/GO:0006096"/>
                  <rdf:li rdf:resource="https://identifiers.org/uniprot/P69905"/>
                </rdf:Bag>
              </bqbiol:is>
            </rdf:Description>
          </rdf:RDF>
        </annotation>
      </species>
    </listOfSpecies>
  </model>
</sbml>`;

const GO = {
  resource: "https://identifiers.org/GO:0006096",
  collection: { prefix: "go", name: "Gene Ontology", homepage: "http://geneontology.org/" },
  identifier: "GO:0006096",
  url: "https://www.ebi.ac.uk/QuickGO/GTerm?id=GO:0006096",
  patternMatch: true,
  providers: [
    { name: "QuickGO", url: "https://www.ebi.ac.uk/QuickGO/GTerm?id=GO:0006096", official: true },
    {
      name: "AmiGO 2",
      url: "https://amigo.geneontology.org/amigo/term/GO:0006096",
      official: false,
    },
  ],
  ontology: {
    ontology: "go",
    label: "glycolytic process",
    iri: "http://purl.obolibrary.org/obo/GO_0006096",
    olsUrl: "https://www.ebi.ac.uk/ols4/ontologies/go/classes?iri=x",
    description: "The breakdown of a carbohydrate into pyruvate.",
    synonyms: ["glycolysis", "a", "b", "c", "d", "e", "f"],
    xrefs: [{ label: "MetaCyc:P341-PWY", url: "https://biocyc.org/x" }],
  },
  chebi: null,
  uniprot: null,
  warnings: [],
  errors: [],
};

const CHEBI = {
  ...GO,
  resource: "https://identifiers.org/CHEBI:31696",
  collection: { prefix: "chebi", name: "ChEBI", homepage: null },
  identifier: "CHEBI:31696",
  url: "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:31696",
  providers: [],
  ontology: null,
  chebi: { formula: "C43H47N2O6S2.Na", charge: 0, mass: "774.981", structure: true },
};

const UNIPROT = {
  ...GO,
  resource: "https://identifiers.org/uniprot/P69905",
  collection: { prefix: "uniprot", name: "UniProt Knowledgebase", homepage: null },
  identifier: "P69905",
  url: "https://www.uniprot.org/uniprot/P69905",
  providers: [],
  ontology: null,
  uniprot: {
    entry: "HBA_HUMAN",
    name: "Hemoglobin subunit alpha",
    organism: "Homo sapiens",
    genes: ["HBA1", "HBA2"],
    length: 142,
    function: "Oxygen transport.",
  },
};

const RESOURCES = [GO, CHEBI, UNIPROT];

test("the inspector shows a card for each resource of an annotation", async ({ page }) => {
  const problems: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" || message.type() === "warning") problems.push(message.text());
  });
  page.on("pageerror", (error) => problems.push(error.message));

  await page.route("**/api/annotation_resource?**", async (route) => {
    const resource = new URL(route.request().url()).searchParams.get("resource");
    const info = RESOURCES.find((candidate) => candidate.resource === resource);
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(info ?? { ...GO, resource, ontology: null }),
    });
  });
  await page.route("**/api/annotation_structure/**", (route) =>
    route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>',
    }),
  );

  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(ANNOTATED_MODEL);
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("report-page")).toBeVisible();
  await page.getByTestId("table-Species").locator("tbody tr[data-pk]").first().click();

  const inspector = page.getByTestId("inspector");
  await expect(inspector.getByTestId("inspector-id")).toHaveText("S1");
  const cards = inspector.getByTestId("annotation-card");
  await expect(cards).toHaveCount(3);

  const go = cards.filter({ hasText: "GO:0006096" });
  await expect(go.getByTestId("annotation-label")).toHaveText("glycolytic process");
  await expect(go.getByTestId("annotation-ontology")).toHaveAttribute("href", GO.ontology.olsUrl);

  const chebi = cards.filter({ hasText: "CHEBI:31696" });
  const structure = chebi.getByTestId("annotation-structure");
  await expect(structure).toBeVisible();
  await expect
    .poll(() =>
      structure.evaluate((img) => (img as unknown as { naturalWidth: number }).naturalWidth),
    )
    .toBeGreaterThan(0);

  await expect(cards.filter({ hasText: "P69905" }).getByTestId("annotation-uniprot")).toContainText(
    "HBA_HUMAN",
  );

  const synonyms = go.getByTestId("annotation-synonyms");
  await expect(synonyms.getByTestId("annotation-synonym")).toHaveCount(5);
  await synonyms.getByTestId("show-all").click();
  await expect(synonyms.getByTestId("annotation-synonym")).toHaveCount(7);

  const identifier = go.getByTestId("annotation-identifier");
  await expect(identifier).toHaveAttribute("target", "_blank");
  await expect(identifier).toHaveAttribute("href", GO.url);

  expect(problems).toEqual([]);
});
