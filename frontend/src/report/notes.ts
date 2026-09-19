import DOMPurify from "dompurify";

/** This module owns its own DOMPurify instance, so the hook below only runs for the notes of a
 * report and never applies to another use of the default, shared instance. */
const purifier = DOMPurify(window);

// an image of the notes gets `referrerpolicy="no-referrer"`, so it never carries the referrer
// of the report to the host that serves it.
purifier.addHook("afterSanitizeAttributes", (node) => {
  if (node.tagName === "IMG") node.setAttribute("referrerpolicy", "no-referrer");
});

/** Sanitises the xhtml of an SBase's notes, and of the message of a constraint, which follows
 * the same restrictions (core §4.10.2), for use with `v-html`. On top of DOMPurify's `html`
 * profile this forbids the elements and attributes real notes do not use: `style`, the form
 * elements (`form`, `input`, `button`, `textarea`, `select`, `option`, `optgroup`, `datalist`,
 * `fieldset`, `legend`, `output`), `dialog`, `audio` and `video`, the attributes that start a
 * form submission or drive a popover or command invoker (`action`, `formaction`, `popover`,
 * `popovertarget`, `popovertargetaction`, `command`, `commandfor`), and `id` and `name`, so an
 * element of the notes never takes the id or name of an element of the app. */
export function sanitizeNotes(html: string): string {
  return purifier.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: [
      "style",
      "form",
      "input",
      "button",
      "textarea",
      "select",
      "option",
      "optgroup",
      "datalist",
      "fieldset",
      "legend",
      "output",
      "dialog",
      "audio",
      "video",
    ],
    FORBID_ATTR: [
      "action",
      "formaction",
      "popover",
      "popovertarget",
      "popovertargetaction",
      "command",
      "commandfor",
      "id",
      "name",
    ],
  });
}

/** Whether the notes of an element show a reader anything once they are sanitised: a text or an
 * image. Notes which hold an empty body, or nothing but markup the report does not allow, are
 * as empty as no notes, and the inspector gives them no section. */
export function hasNotes(html: string | null | undefined): boolean {
  if (!html) return false;
  const holder = document.createElement("template");
  holder.innerHTML = sanitizeNotes(html);
  return (
    (holder.content.textContent ?? "").trim() !== "" || holder.content.querySelector("img") !== null
  );
}
