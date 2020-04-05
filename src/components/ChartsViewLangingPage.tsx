import React from "react";

export const ChartsViewLandingPage: React.StatelessComponent<{}> = () => {
  return <>
    <div className="card landing-card">
      <div>
        <h4>Load Data</h4>
        <p>To load data, use <span className="code">m.from_file("path/to/your_data.csv")</span>, the columns will show up to the right.</p>
        <h4>Load Charts</h4>
        <p>For any dataframes, you can visualize it here with <span className="code">.vis()</span>.</p>
        <h4>Making Interactions</h4>
        <p>
          All the loaded charts by default are augmented with interactivity. You can <b>zoom</b> by <span className="action-instruction">scrolling</span> your mouse, <b>pan</b> by dragging the view.
          You can also <b>select</b> a subset of the data by <b><span className="action-instruction">shift click</span></b> with a bar chart, or <span className="action-instruction">shift-drag</span> to draw the brush, with a scatter plot or line chart.
        </p>
        <h4>Recording/Restoring Interactions</h4>
        <p>
          By default, your interactions are executed via a "log" in a code cell to the left.  You can look at the code to get a sense of what you have interacted with.  You can also execute the code by uncommenting the relevant selections.
        </p>
        <h4>Toggle and Resize Panes</h4>
        <p>
          To toggle this pane (restoring the traditional notebook view), click on <b>Toggle Midas</b>, from the menu bar on the top. Similarly, you can click <b>Toggle Column Shelf</b> to just hide the pane to the right.
        </p>
        <p>To resize, you can also drag the left edge of the the main (blue)pane---the resizer will be highlighted with a darker shade of blue when you hover over.</p>
        <br></br>
      </div>
    </div>
  </>;
};