"""make sure that the synthesized interactions are working as expected
"""

import unittest
import pandas as pd

from midas import Midas
DF_NAME = 'simple_df'


class TestLinking(unittest.TestCase):
    def test_simple(self):
        m = Midas()
        df = pd.DataFrame([[1,2,0,12], [3,4,0,11], [5,6,1, 9], [7,8,1,10], [9,10,0,10]], columns=['a', 'b', 'c', 'd'])
        m.register_df(df, DF_NAME)
        m.loc(DF_NAME, 'ad_df', columns=['a', 'd'])
        m.loc(DF_NAME, 'bc_df', columns=['b', 'c'])
        m.link('ad_df', 'bc_df')
        # now add interaction filter
        val_str = '{"x":[2, 4], "y": [3,15]}'
        # now start one iteration of the loop
        m.js_add_selection('ad_df', val_str)
        # now assert that 'bc_df' is [4,0]
        bc_df = m.dfs['bc_df'].df
        self.assertEqual(len(bc_df.index), 1)
        self.assertTrue(bc_df.iloc[0]['b'] == 4)
        self.assertTrue(bc_df.iloc[0]['c'] == 0)
        m.js_add_selection('ad_df', "null")
        bc_df2 = m.dfs['bc_df'].df
        self.assertEqual(len(bc_df2.index), 5)
        self.assertTrue(bc_df2.iloc[0]['b'] == 2)
        self.assertTrue(bc_df2.iloc[0]['c'] == 0)


if __name__ == '__main__':
    unittest.main()

