/** The repository of the application, where it is developed, released and discussed. */
export const REPOSITORY_URL = "https://github.com/matthiaskoenig/sbml4humans";

/** The release of a version on GitHub, whose body are the release notes of that version. A build
 * between two releases carries the version of the release before it. */
export function releaseUrl(version: string): string {
  return `${REPOSITORY_URL}/releases/tag/${version}`;
}

export function commitUrl(commit: string): string {
  return `${REPOSITORY_URL}/commit/${commit}`;
}
