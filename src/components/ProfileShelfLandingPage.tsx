import React from "react";


export const ProfileShelfLandingPage: React.StatelessComponent<{}> = () => {
  return <div>
    <div className="landing-card">
      <p>Once you load data <pre>m.read_table("your_data.csv")</pre></p>, the columns will show up here.  To quickly investigate the interesting columes, click on the column name to generate the <b>code</b> and the <b>charts</b>. For columns of little value, click the cross icon to hide the column.
    </div>
  </div>;
};