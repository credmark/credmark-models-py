import os
import sys
import unittest
from unittest import TestCase
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level='DEBUG')


class TestAddress(TestCase):
    def test_run(self):
        sys.path.insert(0, os.path.join('..', 'credmark-model-framework-py'))
        from credmark.cmf.model import Model, ModelContext

        import credmark.cmf.credmark_dev

        credmark.cmf.credmark_dev.main()

        compose.map-block-time-series \
        '{"modelSlug": "price.oracle-chainlink",
          "modelInput": {"base": {"address": "0xD533a949740bb3306d119CC777fa900bA034cd52"}},
          "endTimestamp": 1645446694,
          "interval": 86400,
          "count": 3,
          "exclusive": true}'


if __name__ == '__main__':
    unittest.main()
