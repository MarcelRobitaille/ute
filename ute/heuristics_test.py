import io
import unittest

import pandas as pd

from .heuristics import is_sparse, filter_group


def load(text: str):
    return pd.read_fwf(io.StringIO(text))


class HeuristicsTestCase(unittest.TestCase):
    def test_is_sparse(self):
        df = load("""
            level  block_num  par_num  line_num  word_num  left  top  width  height           text
                5          5        1         1         1   378  555     99      32          XXXXX
                5          5        1         1         2   802  575      1       3              X
                5          5        1         2         1   378  603    120      32         XXXXXX
                5          5        1         2         2   513  602    131      40         XXXXXX
                5          5        1         2         3   661  602    145      32      XXXXXXXXX
                5          5        1         3         1   378  651    223      32  XXXXXXXXXXXXX
                5          5        1         3         2   621  650     40      32             XX
                5          5        2         1         1   377  699    112      33          XXXXX
                5          5        2         1         2   502  699    178      40       XXXXXXXX
        """)
        self.assertTrue(is_sparse(df))

    def test_filter_group(self):
        df = load("""
            level  block_num  par_num  line_num  word_num  left  top  width  height              text
                5          6        1         1         1   259  600    252      26  XXXXXXXXXXXXXXXX
        """)
        self.assertTrue(filter_group(df))

        df = load("""
            level  block_num  par_num  line_num  word_num  left   top  width  height             text
                5          2        1         1         1    44  1291     20     223 XXXXXXXXXXXXXXXX
        """)
        self.assertFalse(filter_group(df))


if __name__ == "__main__":
    unittest.main()
