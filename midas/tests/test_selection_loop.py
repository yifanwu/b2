from midas.midas_algebra.dataframe import MidasDataFrame
from pandas import DataFrame
import unittest
from typing import cast

from midas import Midas
from midas.vis_types import ChartType, TwoDimSelectionPredicate
from midas.event_types import TickIOType
from midas.state_types import DFName

DF_NAME = 'simple_df'
DERIVED_DF_NAME = DFName('derived_df')

def df_trans(df_in: MidasDataFrame):
    df_out = df_in.select(df_in.a > 2) # type: ignore
    return df_out


class TestSelections(unittest.TestCase):
    def test_simple(self):
        m = Midas()
        df = DataFrame([[1,2], [3,4], [5,6]], columns=['a', 'b'])
        m.register_df(df, DF_NAME)

        steps = 0
        def cb(predicate):
            nonlocal steps
            steps += 1
            if (steps == 1):
                print('\n> unit test started for step 1')
                self.assertEqual(predicate.x[0], 2)
                # assert that the df_trans is set properly
                mdf = m.get_df_info(DERIVED_DF_NAME)
                derived_df = mdf.df.value
                print(derived_df)
                # 1 row
                self.assertEqual(derived_df.value[0], 1)
                # 1 column
                self.assertEqual(derived_df.shape[1], 1)
                self.assertEqual(derived_df.iloc[0]['c'], 7)
                self.assertEqual(len(m.dfs[DF_NAME].predicates), 1)
                self.assertIsInstance(m.dfs[DF_NAME].predicates[0], TwoDimSelectionPredicate)
                _p = cast(TwoDimSelectionPredicate, m.dfs[DF_NAME].predicates[0])
                self.assertEqual(_p.x[0], 2)
                self.assertEqual(_p.x_column, 'a')
                # make sure that the visual specs are created for 'derived_df'
                visualization = m.get_df_vis_info(DERIVED_DF_NAME)
                self.assertIsNotNone(visualization)
                # make sure that this is scatter plot
                self.assertEqual(m.dfs[DERIVED_DF_NAME].visualization.chart_info.chart_type, ChartType.bar_linear)
            elif (steps == 2):
                print('\n> unit test started for step 2')
                self.assertEqual(predicate.x[0], 0)
                # assert that the df_trans is set properly
                derived_df_2 = m.get_df(DERIVED_DF_NAME)
                print(derived_df_2)
                # 1 row
                self.assertEqual(derived_df_2.shape[0], 2)
                # 1 column
                self.assertEqual(derived_df_2.shape[1], 1)
                self.assertEqual(derived_df_2.iloc[0]['c'], 3)
                self.assertEqual(derived_df_2.iloc[1]['c'], 7)
                self.assertEqual(len(m.dfs[DF_NAME].predicates), 2)
                self.assertIsInstance(m.dfs[DF_NAME].predicates[1], TwoDimSelectionPredicate)
                _p = cast(TwoDimSelectionPredicate, m.dfs[DF_NAME].predicates[1])
                self.assertEqual(_p.x[0], 0)
                self.assertEqual(_p.x_column, 'a')
            print('unit test completed\n')
        m.bind(TickIOType.data, TickIOType.data, DF_NAME, DERIVED_DF_NAME)(df_trans)
        # note that this has to come after the first callback, since it will otherwise not get called
        m.bind(TickIOType.predicate, TickIOType.void, DF_NAME)(cb)
        cb_items = m.tick_funcs.get(DF_NAME)
        self.assertIsNotNone(cb_items)
        if cb_items:
            self.assertEqual(len(cb_items), 2)

        val_str = '{"x":[2, 4],"y":[3, 5]}'
        # now start one iteration of the loop
        m.js_add_selection("simple_df", val_str)
        # sleep(1)
        # now start the second iteration of the loop
        val_str_2 = '{"x":[0, 4],"y":[1, 5]}'
        m.js_add_selection("simple_df", val_str_2)
    
    # def test_create_chart_after(self):
    #     m = Midas()
    #     df = pd.DataFrame([[1,2], [3,4], [5,6]], columns=['a', 'b'])
    #     m.register_df(df, DF_NAME)
    #     steps = 0
    #     def cb(predicate):
    #         nonlocal steps
    #         steps += 1
    #     # note that this has to come after the first callback, since it will otherwise not get called
    #     m.add_callback_to_selection(DF_NAME, cb)
    #     val_str = '{"x":[2, 4],"y":[3, 5]}'
    #     # now start one iteration of the loop
    #     m.js_add_selection("simple_df", val_str)
    #     m.new_visualization_from_selection(DF_NAME, 'derived_df', df_trans)
        


if __name__ == '__main__':
    unittest.main()

