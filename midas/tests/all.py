import unittest

from midas.tests.test_selection_loop import TestSelections
from midas.tests.test_linking import TestLinking


if __name__ == '__main__':
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite(map(loader.loadTestsFromTestCase, [TestLinking, TestSelections]))
    runner.run(suite)
