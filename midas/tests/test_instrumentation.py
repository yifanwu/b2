from midas.types import OpType, OpLogItem
import unittest
from midas.context import Context
from midas.state import State
import pandas as pd

# TODO for RYAN
class TestInstrumentation(unittest.TestCase):
    def test_loaders(self):
        s = State()
        c = Context(s)
        # now i call pandas functions
        df = pd.read_csv("data/dummy.csv")
        self.assertEqual(len(c.op_log), 1)
        # TODO

    def test_loc(self):
        s = State()
        c = Context(s)
        df = pd.read_csv("data/dummy.csv")
        def assertProjection(op: OpLogItem):
            self.assertEqual(item.op, OpType.projection)
            # the following you can decide, doesn't have to be loc
            self.assertEqual(item.fun_name, "loc")
            self.assertEqual(item.src_name, "df")
            self.assertEqual(item.dest_name, "df_a")
        
        df_a = df[['a']]
        self.assertEqual(len(c.op_log), 1)
        item = c.op_log[0]
        assertProjection(item)
        df_a2 = df.a
        self.assertEqual(len(c.op_log), 2)
        item1 = c.op_log[1]
        assertProjection(item1)
        
        df_first = df[df['a'] == 1]
        self.assertEqual(len(c.op_log), 3)
        item = c.op_log[2]
        self.assertEqual(item.op, OpType.selection)
        # the following you can decide, doesn't have to be loc
        self.assertEqual(item.fun_name, "loc")
        self.assertEqual(item.src_name, "df")
        self.assertEqual(item.dest_name, "df_first")
    
        
    