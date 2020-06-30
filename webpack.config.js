var webpack = require("webpack");

const commonConfig = {
  resolve: {
    extensions: [".ts", ".tsx", ".js"]
  },
  devtool: "source-map",
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader"
      }, {
        test: /\.css$/,
        loader: ['style-loader', "css-loader"]
      }
    ]
  }
};

const outputPath = __dirname + "/b2/static";
const outputLibraryTarget = "amd";

module.exports = [
  Object.assign({}, commonConfig, {
    entry: "./src/index.tsx",
    output: {
      filename: "index.js",
      library: "nbextensions/b2/index",
      path: outputPath,
      libraryTarget: outputLibraryTarget
    }
  }),
];
