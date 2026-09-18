import { expect, test } from "@playwright/test";

/** A model whose notes carry markup outside the set `sanitizeNotes` allows: a `<style>` element,
 * a `position: fixed` element that overlaps the app bar, a form, and a paragraph and an image
 * that are the actual content of the notes. The attribute selector inside the `<style>` element
 * is unquoted because libsbml escapes quotes inside a `<style>` element of a notes string. The
 * image is a data uri so the test does not depend on the network. */
const MODEL = `<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version1/core" level="3" version="1">
  <model metaid="meta_notes_test" id="notes_test" name="notes security test">
    <notes>
      <body xmlns="http://www.w3.org/1999/xhtml">
        <style>[data-testid=app-bar]{background:rgb(255, 0, 0) !important;}</style>
        <div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;background:#fff">
          <form>
            <input type="password"/>
            <button>submit</button>
          </form>
        </div>
        <p data-testid="notes-paragraph">hello notes</p>
        <img data-testid="notes-image" alt="a picture" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="/>
      </body>
    </notes>
    <listOfCompartments>
      <compartment id="c" constant="true"/>
    </listOfCompartments>
  </model>
</sbml>
`;

test("the notes of an element stay inside their box and keep only the allowed markup", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByTestId("home-tab-paste").click();
  await page.getByTestId("paste-input").fill(MODEL);
  await page.getByTestId("paste-submit").click();
  await expect(page.getByTestId("report-page")).toBeVisible();

  await page.getByTestId("bar-model").click();
  const inspector = page.getByTestId("inspector");
  await expect(inspector.getByTestId("inspector-type")).toHaveText("Model");

  const notes = inspector.getByTestId("notes");
  await expect(notes).toBeVisible();
  const notesHtml = await notes.innerHTML();
  expect(notesHtml).not.toContain("<style");
  expect(notesHtml).not.toContain("<form");
  expect(notesHtml).not.toContain("<input");
  expect(notesHtml).not.toContain("<button");

  const appBar = page.getByTestId("app-bar");
  await expect(appBar).toHaveCSS("background-color", "rgb(255, 255, 255)");

  // the element at the centre of the app bar is inside the app bar itself, so nothing painted by
  // the notes (such as the position:fixed element above) reaches that point; a single evaluate
  // call, so a regression fails immediately instead of waiting out an actionability timeout.
  const centreIsInsideAppBar = await appBar.evaluate((element) => {
    const rect = element.getBoundingClientRect();
    const point = element.ownerDocument.elementFromPoint(
      rect.x + rect.width / 2,
      rect.y + rect.height / 2,
    );
    return element.contains(point);
  });
  expect(centreIsInsideAppBar).toBe(true);

  await expect(notes.getByTestId("notes-paragraph")).toBeVisible();
  await expect(notes.getByTestId("notes-image")).toBeVisible();
});
