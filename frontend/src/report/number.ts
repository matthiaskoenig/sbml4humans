/** The doubles of the report, which may be infinite or not a number.
 *
 * SBML writes `INF`, `-INF` and `NaN` for the three values of a double which are no ordinary
 * number (core §3.1.5), and JSON has no literal for any of them. The api therefore sends them
 * as the strings pydantic defines (`ser_json_inf_nan`), so every double of the report is a
 * number or one of these three constants, and `null` means what it says: the file does not set
 * the attribute at all. */
export const NUMBER_CONSTANTS: Readonly<Record<string, number>> = {
  Infinity: Number.POSITIVE_INFINITY,
  "-Infinity": Number.NEGATIVE_INFINITY,
  NaN: Number.NaN,
};

/** A double of the report as the JSON carries it. */
export type ReportNumber = number | "Infinity" | "-Infinity" | "NaN";

/** The number a value of the report stands for, `null` for everything which is no double:
 * `null`, `undefined` and the text of a string field. */
export function toNumber(value: unknown): number | null {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value in NUMBER_CONSTANTS) {
    return NUMBER_CONSTANTS[value] ?? null;
  }
  return null;
}

/** How a double reads: the sign of infinity with its direction, `NaN` for a value which is not
 * a number, and six significant digits for every ordinary number. */
export function formatNumber(value: number): string {
  if (Number.isNaN(value)) return "NaN";
  if (value === Number.POSITIVE_INFINITY) return "∞";
  // the minus of a negative number of the report is the hyphen `String(-15)` writes, and
  // the two stand next to each other in one column
  if (value === Number.NEGATIVE_INFINITY) return "-∞";
  return Number.isInteger(value) ? String(value) : String(Number(value.toPrecision(6)));
}

/** What the file writes for a double the report shows as a sign, as the tooltip of that sign.
 * An ordinary number and a `NaN` read the same in the file as in the report and need none. */
export function numberTooltip(value: number): string | undefined {
  if (value === Number.POSITIVE_INFINITY) return "INF";
  if (value === Number.NEGATIVE_INFINITY) return "-INF";
  return undefined;
}
