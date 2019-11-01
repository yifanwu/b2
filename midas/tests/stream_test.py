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
        mdf = m.register_df(df, DF_NAME)

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
        stream = m.get_stream(DF_NAME)
        stream.add_callback(cb)
        def transform(predicates):
            # takes in predicates
            new_mdf = predicates.filter(mdf)
            new_mdf.project[new_mdf.b].assign(DERIVED_DF_NAME)
        stream.add_callback(transform)
        val_str = '{"x":[2, 4],"y":[3, 5]}'
        # now start one iteration of the loop
        m.add_selection("simple_df", val_str)
        # sleep(1)
        # now start the second iteration of the loop
        val_str_2 = '{"x":[0, 4],"y":[1, 5]}'
        m.add_selection("simple_df", val_str_2)


if __name__ == '__main__':
    unittest.main()

