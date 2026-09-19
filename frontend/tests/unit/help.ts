/** The key of the entry a help link opens. Every one of them is a real anchor whose href is the
 * route of the report with `help=<key>`, which is what the dialog reads, so the href is where a
 * test asks which entry a label, a column header or a heading explains. */
export function helpKeyOf(href: string | undefined): string | null {
  return new URL(href ?? "", "http://localhost").searchParams.get("help");
}
