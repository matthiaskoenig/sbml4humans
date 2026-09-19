/** Whether a click on a link is the plain left click a component may answer itself: the left
 * button and no modifier key. Every other click, a right click, a middle click or one held with a
 * modifier key, belongs to the browser, so that ctrl-click, shift-click and middle-click open the
 * href in a new tab or window the way a reader expects of a real link. The links of the help
 * dialog are real links, the ones a description carries (`HelpMarkdown.vue`) and the ones the
 * dialog builds itself (`HelpLink.vue`), and they share this test so that the two can never judge
 * the same click differently. */
export function isPlainClick(event: MouseEvent): boolean {
  return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
}
