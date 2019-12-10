import React from "react";

export const ChartsViewLandingPage: React.StatelessComponent<{}> = () => {
  return <>
    <div className="card landing-card">
      <b><b>charts</b> will be shown here.</b>
      <br></br>
      <p>
        You can <b>zoom</b> by <span className="action-instruction">scrolling</span> your mouse.
        You can also <b>select</b> a subset of the data by <span className="action-instruction">shift click</span>, then <span className="action-instruction">drag</span> to draw the brush.
      </p>
      <p>
        You can also save the selections you've made to the left. When you click on a selection, you can go back and restore the state.
      </p>
      <br></br>
      <p>To load data, use <span className="code">m.read_table("your_data.csv")</span>, the columns will show up in the pannel to the left.  To quickly investigate the interesting columes, click on the column name to generate the <b>code</b> and the <b>charts</b>. For columns of little value, click the cross icon to hide the column.</p>
    </div>
  </>;
};