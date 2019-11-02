import unittest
from midas import Midas
import pandas as pd

DF_NAME = 'simple_df'


class TestSelections(unittest.TestCase):
    def test_simple(self):
        m = Midas()
        simple_df = pd.DataFrame([[1,2], [3,4], [5,6]], columns=['a', 'b'])
        m.register_df(DF_NAME, simple_df)
        m.js_add_selection(DF_NAME, '{"x":[2, 4],"y":[3, 5]}')
        c = m.js_get_current_chart_code(DF_NAME)
        # evaluate c and make sure it's the same 
        df = eval(c)
        expected_df = m.get_current_selection(DF_NAME, "data")
        self.assertTrue(df.equals(expected_df))

if __name__ == '__main__':
    unittest.main()