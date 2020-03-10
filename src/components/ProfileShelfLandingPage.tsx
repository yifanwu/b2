import React from "react";

export const ProfileShelfLandingPage: React.StatelessComponent<{}> = () => {
  return <div>
    <div className="card landing-card">
      <h4>Column Shelf</h4>
      <p><b>Columns</b> of loaded data will show here. You can click on the x symbol to the right to hide the column from view.</p>
      <h4>See Distributions</h4>
      <p>You can <b>click on the column</b> to get the distribution of the data.</p>
    </div>
  </div>;
};