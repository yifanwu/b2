from midas.util.errors import debug_log
from midas.midas_algebra.dataframe import MidasDataFrame
from pandas import DataFrame
import unittest
from typing import cast

from midas import Midas
from midas.vis_types import ChartType, TwoDimSelectionPredicate
from midas.state_types import DFName

DF_NAME = 'simple_df'
DERIVED_DF_NAME = DFName('derived_df')

def df_trans(df_in: MidasDataFrame):
    df_out = df_in.select(df_in.a > 2) # type: ignore
    return df_out


class TestStream(unittest.TestCase):
    def test_simple(self):
        m = Midas()
        df = DataFrame([[1,2], [3,4], [5,6]], columns=['a', 'b'])
        simple_df = m.register_df(DF_NAME, df)

        steps = 0
        def cb(predicate):
            nonlocal steps
            steps += 1
            if (steps == 1):
                print('\n> unit test started for step 1')
                self.assertEqual(predicate.x[0], 2)
                # assert that the df_trans is set properly
                derived_df_info = m.get_df_info(DERIVED_DF_NAME)
                self.assertIsNotNone(derived_df_info, f"{DERIVED_DF_NAME} should be found!")
                # Note: cannot use value here because some scoping issues
                derived_df_value = derived_df_info.df.pandas_value
                print("Derived_df results")
                print(derived_df_value)
                # 1 row
                # 1 column
                self.assertEqual(derived_df_value.shape[0], 1)
                self.assertEqual(derived_df_value.shape[1], 1)
                self.assertEqual(derived_df_value.iloc[0]['b'], 4)
                self.assertIsInstance(predicate, TwoDimSelectionPredicate)
                _p = cast(TwoDimSelectionPredicate, predicate)
                self.assertEqual(_p.x[0], 2)
                self.assertEqual(_p.x_column, 'a')
                # make sure that the visual specs are created for 'derived_df'
                visualization = m.get_df_vis_info(DERIVED_DF_NAME)
                self.assertIsNotNone(visualization)
                # make sure that this is scatter plot
                self.assertEqual(visualization.chart_type, ChartType.bar_linear)
            elif (steps == 2):
                print('\n> unit test started for step 2')
                self.assertEqual(predicate.x[0], 0)
                self.assertIsInstance(predicate, TwoDimSelectionPredicate)
                _p = cast(TwoDimSelectionPredicate, predicate)
                self.assertEqual(_p.x[0], 0)
                self.assertEqual(_p.x_column, 'a')
            print('unit test completed\n')

        # get the stream, and bind to it
        debug_log("getting stream")
        stream = m.get_stream(DF_NAME)
        debug_log("adding callbakc")
        def transform(predicate):
            debug_log(f"Transform {predicate}")
            new_mdf = simple_df.apply_selection(predicate)
            new_mdf.project([new_mdf.b]).assign(DERIVED_DF_NAME) # type: ignore
        stream.add_callback(transform)

        # this should be added after the first one since there is a dependency!
        stream.add_callback(cb)
        
        # 1
        val_str = '{"x":[2, 4],"y":[3, 5]}'
        m.add_selection("simple_df", val_str)
        # 2
        val_str_2 = '{"x":[0, 4],"y":[1, 5]}'
        m.add_selection("simple_df", val_str_2)


if __name__ == '__main__':
    unittest.main()

