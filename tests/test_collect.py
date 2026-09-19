import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import collect as c

SECRET = 'ab' * 16
LINK = f'tg://proxy?server=example.org&port=443&secret={SECRET}'

class CollectorTests(unittest.TestCase):
    def test_normalize_and_dedupe(self):
        alternate = f'https://t.me/proxy?secret={SECRET.upper()}&amp;port=0443&amp;server=EXAMPLE.ORG&comment=ignored'
        self.assertEqual(c.extract(LINK + '\n' + alternate), {LINK})

    def test_bad_links(self):
        for raw in [LINK.replace('443', '0'), LINK.replace('example.org', 'bad host'), LINK + '&port=80', LINK.replace(SECRET, 'short')]:
            self.assertIsNone(c.proxy_link(raw))

    def test_sources(self):
        self.assertEqual(c.source_urls('https://github.com/owner/repo/blob/main/list.txt\nhttps://raw.githubusercontent.com/owner/repo/refs/heads/main/list.txt'), ['https://raw.githubusercontent.com/owner/repo/main/list.txt'])
        with self.assertRaises(ValueError):
            c.source_urls('http://example.org/list')

    def test_total_failure_preserves_previous(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'proxies.txt'
            p.write_text('previous\n')
            with patch.object(c, 'fetch', return_value=set()):
                with self.assertRaises(ValueError):
                    c.collect('https://example.org/private', p)
            self.assertEqual(p.read_text(), 'previous\n')

    def test_partial_success_and_no_source_logging(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'proxies.txt'
            out = io.StringIO()
            with patch.object(c, 'fetch', side_effect=[{LINK}, set()]), contextlib.redirect_stdout(out):
                c.collect('https://example.org/private1\nhttps://example.org/private2', p)
            self.assertEqual(p.read_text(), LINK + '\n')
            self.assertNotIn('example.org', out.getvalue())
            self.assertIn('warning', out.getvalue())

    def test_request_error_does_not_leak(self):
        out = io.StringIO()
        with patch.object(c, 'urlopen', side_effect=OSError('https://secret.example/private')), patch.object(c.time, 'sleep'), contextlib.redirect_stdout(out):
            self.assertEqual(c.fetch('https://secret.example/private'), set())
        self.assertEqual(out.getvalue(), '')

if __name__ == '__main__':
    unittest.main()
