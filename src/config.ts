/**
 * Returns the DOM id of the given element that contains the visualizations
 * @param dfName the name of the data frame of the visualization
 * @param includeSelector whether to include CSS selector (#)
 */
export function makeElementId(dfName: string, includeSelector: boolean = false) {
  let toReturn = `midas-element-${dfName}`;
  return includeSelector ? "#" + toReturn : toReturn;
}
