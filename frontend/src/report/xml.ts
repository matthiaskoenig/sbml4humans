/** The highlighting of the XML of an element: a scanner which splits the XML into tokens of a
 * kind each, in one pass and without a regular expression which could backtrack, so that a
 * large annotation costs time linear in its length. The XML is written by libsbml and well formed,
 * but the scanner does not rely on it: whatever it does not recognise is text, and every character
 * of the input is in exactly one token, so the tokens joined are the input. */

/** The kinds of a token: the punctuation of a tag (`<`, `</`, `>`, `/>`, `=`), the namespace
 * prefix of a name with its colon, the name of an element, the name of an attribute, the quoted
 * value of an attribute, the text, an entity reference, and every other markup (a comment, a
 * CDATA section, a processing instruction, a declaration). */
export type XmlTokenKind =
  "punct" | "prefix" | "name" | "attribute" | "value" | "text" | "entity" | "markup";

export interface XmlToken {
  kind: XmlTokenKind;
  text: string;
}

/** One line of the XML: its tokens and the number of the white space characters it starts
 * with, which the view uses to hang the continuation of a wrapped line below its content. */
export interface XmlLine {
  indent: number;
  tokens: XmlToken[];
}

const WHITESPACE = /\s/;
const ENTITY = /^&#?[\w.-]{1,32};/;
const NAME_START = /[A-Za-z_:]/;

function isSpace(char: string | undefined): boolean {
  return char !== undefined && WHITESPACE.test(char);
}

/** Splits XML into its tokens. */
export function tokenizeXml(xml: string): XmlToken[] {
  const tokens: XmlToken[] = [];
  const n = xml.length;
  let i = 0;

  const push = (kind: XmlTokenKind, end: number): void => {
    if (end <= i) return;
    const text = xml.slice(i, end);
    const last = tokens[tokens.length - 1];
    if (last?.kind === kind && kind === "text") last.text += text;
    else tokens.push({ kind, text });
    i = end;
  };
  /** The end of markup closed by `close`, or the end of the input when it is not closed. */
  const until = (close: string, from: number): number => {
    const at = xml.indexOf(close, from);
    return at < 0 ? n : at + close.length;
  };
  /** The end of the run of characters from `from` which `inRun` accepts. */
  const run = (from: number, inRun: (char: string) => boolean): number => {
    let end = from;
    while (end < n && inRun(xml.charAt(end))) end++;
    return end;
  };
  const isNameChar = (char: string): boolean =>
    !isSpace(char) && char !== "=" && char !== "/" && char !== ">" && char !== "<";

  /** A name of an element or an attribute, its prefix apart. */
  const pushName = (kind: "name" | "attribute", end: number): void => {
    const colon = xml.slice(i, end).indexOf(":");
    if (colon > 0 && colon < end - i - 1) push("prefix", i + colon + 1);
    push(kind, end);
  };

  /** A tag from its `<` or `</`, up to its `>` or `/>`, or to the end of the input. */
  const pushTag = (): void => {
    push("punct", xml[i + 1] === "/" ? i + 2 : i + 1);
    pushName("name", run(i, isNameChar));
    while (i < n) {
      if (isSpace(xml[i])) {
        push("text", run(i, isSpace));
      } else if (xml[i] === ">") {
        push("punct", i + 1);
        return;
      } else if (xml.startsWith("/>", i)) {
        push("punct", i + 2);
        return;
      } else if (xml[i] === "<") {
        // a tag which is not closed: the next one starts here
        return;
      } else if (xml[i] === "/" || xml[i] === "=") {
        push("text", i + 1);
      } else {
        pushName("attribute", run(i, isNameChar));
        const equals = run(i, isSpace);
        if (xml[equals] !== "=") continue;
        push("punct", run(equals + 1, isSpace));
        const quote = xml[i];
        if (quote === '"' || quote === "'") {
          const close = xml.indexOf(quote, i + 1);
          push("value", close < 0 ? n : close + 1);
        }
      }
    }
  };

  while (i < n) {
    if (xml.startsWith("<!--", i)) push("markup", until("-->", i + 4));
    else if (xml.startsWith("<![CDATA[", i)) push("markup", until("]]>", i + 9));
    else if (xml.startsWith("<?", i)) push("markup", until("?>", i + 2));
    else if (xml.startsWith("<!", i)) push("markup", until(">", i + 2));
    else if (
      xml[i] === "<" &&
      NAME_START.test(xml[i + 1] === "/" ? (xml[i + 2] ?? "") : (xml[i + 1] ?? ""))
    ) {
      pushTag();
    } else if (xml[i] === "&") {
      const entity = ENTITY.exec(xml.slice(i, i + 36));
      push(entity ? "entity" : "text", i + (entity ? entity[0].length : 1));
    } else {
      push(
        "text",
        run(i + 1, (char) => char !== "<" && char !== "&"),
      );
    }
  }
  return tokens;
}

/** The lines of XML, a token which spans lines (a text, a comment) split at them. */
export function xmlLines(xml: string): XmlLine[] {
  let line: XmlToken[] = [];
  const lines = [line];
  for (const token of tokenizeXml(xml)) {
    token.text.split("\n").forEach((text, index) => {
      if (index > 0) lines.push((line = []));
      if (text) line.push({ kind: token.kind, text });
    });
  }
  return lines.map((tokens) => {
    const text = tokens.map((token) => token.text).join("");
    return { indent: text.length - text.trimStart().length, tokens };
  });
}

/** The parts of an attribute value between which a wrapped line may break: after every `/`,
 * `#`, `?` and `&`, so that a url breaks between its segments rather than inside a word, but
 * never between the slashes of `//` and never next to a quote alone. */
export function valueParts(value: string): string[] {
  return value.split(/(?<=[^"'][/#?&])(?!\/|["']$)/);
}
