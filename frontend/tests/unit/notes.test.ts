import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import NotesView from "@/components/misc/NotesView.vue";
import { sanitizeNotes } from "@/report/notes";

/** The tags and attributes the real notes of the examples use, wrapped the way libsbml returns
 * a notes string (a `<notes>` element around an xhtml `<body>`). */
const REAL_NOTES = `<notes>
  <body xmlns="http://www.w3.org/1999/xhtml">
    <table>
      <tr>
        <td bgcolor="#eeeeee" align="center">a cell</td>
      </tr>
    </table>
    <p style="color: #4183C4">a paragraph</p>
    <a href="https://example.invalid/page" title="a title">a link</a>
    <img src="https://example.invalid/badge.svg" alt="a badge" style="max-width: 100%;"/>
  </body>
</notes>`;

describe("sanitizeNotes", () => {
  it("removes the style element, the form elements, dialog, audio and video", () => {
    const html = sanitizeNotes(`<notes>
      <body xmlns="http://www.w3.org/1999/xhtml">
        <style>body { display: none; }</style>
        <form>
          <input type="password"/>
          <button>submit</button>
          <textarea></textarea>
          <select>
            <optgroup label="a group"><option>x</option></optgroup>
          </select>
          <fieldset><legend>x</legend></fieldset>
          <datalist></datalist>
          <output></output>
        </form>
        <dialog open="">a dialog</dialog>
        <audio src="a.mp3" controls=""></audio>
        <video src="a.mp4" controls=""></video>
        <p>kept text</p>
      </body>
    </notes>`);
    expect(html).not.toContain("<style");
    expect(html).not.toContain("<form");
    expect(html).not.toContain("<input");
    expect(html).not.toContain("<button");
    expect(html).not.toContain("<textarea");
    expect(html).not.toContain("<select");
    expect(html).not.toContain("<optgroup");
    expect(html).not.toContain("<option");
    expect(html).not.toContain("<fieldset");
    expect(html).not.toContain("<legend");
    expect(html).not.toContain("<datalist");
    expect(html).not.toContain("<output");
    expect(html).not.toContain("<dialog");
    expect(html).not.toContain("<audio");
    expect(html).not.toContain("<video");
    expect(html).toContain("kept text");
  });

  it("removes the attributes it forbids from an element it otherwise keeps", () => {
    const html = sanitizeNotes(
      `<p action="https://example.invalid/collect" formaction="https://example.invalid/collect">x</p>` +
        `<div popover="manual" popovertarget="y" popovertargetaction="show">y</div>` +
        `<div commandfor="z" command="show-modal">z</div>` +
        `<p id="app-tooltip" name="note">n</p>`,
    );
    expect(html).toContain("<p>x</p>");
    expect(html).toContain("<div>y</div>");
    expect(html).toContain("<div>z</div>");
    expect(html).toContain("<p>n</p>");
    expect(html).not.toContain("action=");
    expect(html).not.toContain("formaction=");
    expect(html).not.toContain("popover=");
    expect(html).not.toContain("popovertarget=");
    expect(html).not.toContain("popovertargetaction=");
    expect(html).not.toContain("command=");
    expect(html).not.toContain("commandfor=");
    expect(html).not.toContain("id=");
    expect(html).not.toContain("name=");
  });

  it("keeps script, event handlers and javascript hrefs removed as the profile already does", () => {
    const html = sanitizeNotes(
      `<p>x</p><script>alert(1)</script><img src="x" onerror="alert(1)"/><a href="javascript:alert(1)">y</a>`,
    );
    expect(html).not.toContain("<script");
    expect(html).not.toContain("onerror");
    expect(html).not.toContain("javascript:");
  });

  it("keeps the markup and attributes the real notes of the examples use", () => {
    const html = sanitizeNotes(REAL_NOTES);
    expect(html).toContain('<td bgcolor="#eeeeee" align="center">');
    expect(html).toContain('style="color: #4183C4"');
    expect(html).toContain('<a href="https://example.invalid/page" title="a title">');
    expect(html).toContain('src="https://example.invalid/badge.svg"');
    expect(html).toContain('alt="a badge"');
    expect(html).toContain('style="max-width: 100%;"');
  });

  it("sets referrerpolicy on the image so it never reaches the third party via the referrer", () => {
    const html = sanitizeNotes(REAL_NOTES);
    expect(html).toContain('referrerpolicy="no-referrer"');
  });
});

describe("NotesView", () => {
  it("renders the sanitised notes and forbids the style element the profile alone would keep", () => {
    const wrapper = mount(NotesView, {
      props: {
        notes: `<p>hello</p><style>body{display:none}</style><script>alert(1)</script><img src=x onerror=alert(1)>`,
      },
    });
    expect(wrapper.html()).toContain("hello");
    expect(wrapper.html()).not.toContain("<style");
    expect(wrapper.html()).not.toContain("<script");
    expect(wrapper.html()).not.toContain("onerror");
  });
});
