from midas import Midas
import unittest

m = Midas()
cars_df = m.read_json('/Users/yifanwu/Dev/midas/notebooks/cars.json', 'cars_df')

class TestSelections(unittest.TestCase):
    def test_simple(self):
        m.visualize_df_without_spec('cars_df')
        def cb(predicate):
            print("checking predicate", predicate)
            p = predicate.x
            self.assertEqual(p[0], 7)
        m.add_callback_to_selection('cars_df', cb)

        val_str = '{"x":[7, 10],"y":[8, 4]}'
        m.js_add_selection("cars_df", val_str)

if __name__ == '__main__':
    unittest.main()
