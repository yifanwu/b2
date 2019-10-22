import json
import unittest

from midas.midas import Midas
# from midas.showme import gen_spec
from midas.vis_types import ChartType
import pandas as pd

# def _shared_gen_spec(df):
#     spec = gen_spec(df)
#     ps = json.dumps(spec, indent=4)
#     print(ps)

class TestVisualizations(unittest.TestCase):


    def test_basic_flow(self):
        cars_df = pd.read_json('/Users/yifanwu/Dev/midas/notebooks/data/cars.json')
        small_df = cars_df[['Acceleration', 'Origin']].head(5)
        midas = Midas()
        midas.register_df("small_df", small_df)
        self.assertTrue(midas.has_df("small_df"))
        vis = midas.get_df_vis_info("small_df")
        self.assertIsNotNone(vis)
        self.assertEqual(vis.chart_type, ChartType.bar_categorical)


    # def test_agg_categorical(self):
    #     df = pd.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json')
    #     origin_df = df[['Origin']]
    #     self.midas.register_df(origin_df, 'origin_df')
    #     self.assertTrue(self.midas.state.has_df("origin_df"))
    #     self.assertEqual(self.midas.ui_comm.get_chart_type("origin_df"), ChartType.bar_categorical)

    # FIXME: once the integration is done

    # def test_agg_linear(self):
    #     m = Midas()
    #     cars_df = m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json')
    #     m.loc('cars_df', 'displacement_df', columns=['Displacement'])
    #     self.assertTrue(m.state.has_df("displacement_df"))
    #     self.assertEqual(m.ui_comm.get_chart_type("displacement_df"), ChartType.bar_categorical)


    # def test_line_chart(self):
    #     m = Midas()
    #     reviews_df_raw = pd.read_csv('/Users/yifanwu/Dev/midas/notebooks/pitchfork.csv')
    #     reviews_df = reviews_df_raw[['pub_date']]
    #     m.register_df(reviews_df, 'reivews_df')
    #     self.assertIsNotNone(m.dfs["reivews_df"])
    #     self.assertIsNotNone(m.dfs["reivews_df"].visualization)
    #     self.assertIsNotNone(m.dfs["reivews_df"].visualization.chart_info)
    #     self.assertIsNotNone(m.dfs["reivews_df"].visualization.widget)
    #     self.assertEqual(m.dfs["reivews_df"].visualization.chart_info.chart_type, ChartType.line)


if __name__ == '__main__':
    unittest.main()
        