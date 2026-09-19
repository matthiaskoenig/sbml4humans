/** The key of a primary key `<scope>/<type>:<key>`: the id of the element, its meta id or the
 * name its parent gives it, for example `R1.kineticLaw.k`. It is what the report shows for an
 * element without an id, where the whole primary key would repeat the model and the type which
 * the mark in front of it already names. */
export function pkKey(pk: string | null | undefined): string | null {
  if (!pk) return null;
  const colon = pk.indexOf(":");
  return colon === -1 ? pk : pk.slice(colon + 1);
}
