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

const outputPath = __dirname + "/midas/static";
const outputLibraryTarget = "amd";

module.exports = [
  // the main vega extension
  Object.assign({}, commonConfig, {
    entry: "./src/index.ts",
    output: {
      filename: "index.js",
      library: "nbextensions/midas/index",
      path: outputPath,
      libraryTarget: outputLibraryTarget
    }
  }),
  // the widget extension
  Object.assign({}, commonConfig, {
    entry: "./src/widget.ts",
    output: {
      filename: "widget.js",
      path: outputPath,
      libraryTarget: outputLibraryTarget
    },
    externals: {
      "@jupyter-widgets/base": "@jupyter-widgets/base",
      "./index": "nbextensions/midas/index"
    }
  }),
  Object.assign({}, commonConfig, {
    entry: "./src/floater.css",
    output: {
      filename: "floater.css",
      library: "nbextensions/midas/index",
      path: outputPath,
      libraryTarget: outputLibraryTarget
    }
  }),

];
