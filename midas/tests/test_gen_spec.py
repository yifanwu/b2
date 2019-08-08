import json
import unittest

from midas import Midas
from midas.showme import gen_spec
from midas.types import ChartType
import pandas as pd

# def _shared_gen_spec(df):
#     spec = gen_spec(df)
#     ps = json.dumps(spec, indent=4)
#     print(ps)

class TestVisualizations(unittest.TestCase):

    def test_basic_flow(self):
        m = Midas()
        cars_df = pd.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json')
        small_df = cars_df[['Acceleration', 'Origin']].head(5)
        m.register_df(small_df, "small_df")
        self.assertIsNotNone(m.dfs["small_df"])
        self.assertIsNotNone(m.dfs["small_df"].visualization)
        self.assertIsNotNone(m.dfs["small_df"].visualization.chart_info)
        self.assertIsNotNone(m.dfs["small_df"].visualization.widget)

        self.assertEqual(m.dfs["small_df"].visualization.chart_info.chart_type, ChartType.scatter)


    def test_agg_categorical(self):
        m = Midas()
        m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json', 'cars_df')
        m.loc('cars_df', 'origin_df', columns=['Origin'])
        self.assertIsNotNone(m.dfs["origin_df"])
        self.assertIsNotNone(m.dfs["origin_df"].visualization)
        self.assertIsNotNone(m.dfs["origin_df"].visualization.chart_info)
        self.assertIsNotNone(m.dfs["origin_df"].visualization.widget)
        self.assertEqual(m.dfs["origin_df"].visualization.chart_info.chart_type, ChartType.bar_categorical)


    def test_agg_linear(self):
        m = Midas()
        m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json', 'cars_df')
        m.loc('cars_df', 'displacement_df', columns=['Displacement'])
        self.assertIsNotNone(m.dfs["displacement_df"])
        self.assertIsNotNone(m.dfs["displacement_df"].visualization)
        self.assertIsNotNone(m.dfs["displacement_df"].visualization.chart_info)
        self.assertIsNotNone(m.dfs["displacement_df"].visualization.widget)
        self.assertEqual(m.dfs["displacement_df"].visualization.chart_info.chart_type, ChartType.bar_linear)


    def test_line_chart(self):
        m = Midas()
        reviews_df_raw = pd.read_csv('/Users/yifanwu/Dev/midas/notebooks/pitchfork.csv')
        reviews_df = reviews_df_raw[['pub_date']]
        m.register_df(reviews_df, 'reivews_df')
        self.assertIsNotNone(m.dfs["reivews_df"])
        self.assertIsNotNone(m.dfs["reivews_df"].visualization)
        self.assertIsNotNone(m.dfs["reivews_df"].visualization.chart_info)
        self.assertIsNotNone(m.dfs["reivews_df"].visualization.widget)
        self.assertEqual(m.dfs["reivews_df"].visualization.chart_info.chart_type, ChartType.line)


if __name__ == '__main__':
    unittest.main()
        
        