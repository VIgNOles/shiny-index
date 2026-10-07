import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.indexer as indexer


class CollectionGuardTests(unittest.TestCase):
    def test_direct_collection_stops_before_directory_or_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            indexer.write(root / 'source_manifest.json', {'full_collection_enabled': False})
            destination = root / 'new-run'
            with patch.object(indexer, 'ROOT', root), patch.object(indexer, 'urlopen', side_effect=AssertionError('network attempted')):
                with self.assertRaisesRegex(RuntimeError, 'Wiki acquisition disabled'):
                    indexer.collect('https://wikiwiki.jp/shinycolors/テスト', destination)
            self.assertFalse(destination.exists())


if __name__ == '__main__':
    unittest.main()
