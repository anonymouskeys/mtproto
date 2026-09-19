#!/usr/bin/env python3
"""Collect MTProto links. Source URLs must never be printed or persisted."""
import concurrent.futures
import html
import ipaddress
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

MAX_BYTES = 10 * 1024 * 1024
LINK = re.compile(r'(?:tg://proxy\?|https?://(?:t\.me|telegram\.me)/proxy\?)[^\s<>"\'`]+', re.I)


def source_urls(value):
    result = set()
    for line in value.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        p = urlsplit(line)
        if p.scheme != 'https' or not p.hostname or p.username or p.password:
            raise ValueError('Invalid source configuration')
        parts = p.path.split('/')
        if p.hostname == 'github.com' and len(parts) >= 6 and parts[3] == 'blob':
            p = p._replace(netloc='raw.githubusercontent.com', path='/'.join(parts[:3] + parts[4:]))
        if p.hostname == 'raw.githubusercontent.com':
            p = p._replace(path=p.path.replace('/refs/heads/', '/'))
        result.add(urlunsplit(p._replace(fragment='')))
    if not result or len(result) > 100:
        raise ValueError('Invalid source configuration')
    return sorted(result)


def proxy_link(raw):
    try:
        q = parse_qs(urlsplit(raw).query, keep_blank_values=True)
        if any(len(q.get(k, [])) != 1 for k in ('server', 'port', 'secret')):
            return None
        server, port, secret = (q[k][0] for k in ('server', 'port', 'secret'))
        server = server.strip('[]').lower().rstrip('.')
        try:
            server = str(ipaddress.ip_address(server))
        except ValueError:
            server = server.encode('idna').decode('ascii')
            if len(server) > 253 or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', x) for x in server.split('.')):
                return None
        if not port.isascii() or not port.isdigit() or not 1 <= int(port) <= 65535:
            return None
        # Accept hex and URL-safe Base64 secrets; no MTProto handshake is claimed.
        if not re.fullmatch(r'[A-Za-z0-9_+/-]{20,512}={0,2}', secret):
            return None
        if re.fullmatch(r'[a-fA-F0-9]+', secret):
            secret = secret.lower()
        return 'tg://proxy?' + urlencode({'server': server, 'port': str(int(port)), 'secret': secret})
    except (ValueError, UnicodeError):
        return None


def extract(value):
    return {p for raw in LINK.findall(html.unescape(value)) if (p := proxy_link(raw))}


def fetch(url):
    for attempt in range(3):
        try:
            req = Request(url, headers={'User-Agent': 'mtproto-collector/1.0'})
            with urlopen(req, timeout=25) as response:
                if urlsplit(response.url).scheme != 'https':
                    return set()
                body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return set()
            return extract(body.decode('utf-8-sig', errors='replace'))
        except Exception:
            # Exceptions may contain confidential source URLs. Never log them.
            if attempt < 2:
                time.sleep(attempt + 1)
    return set()


def collect(value, output=Path('proxies.txt')):
    urls = source_urls(value)
    merged = set()
    failed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for links in pool.map(fetch, urls):
            if not links:
                failed += 1
            merged.update(links)
    if not merged:
        raise ValueError('No proxies collected; previous output preserved')
    content = '\n'.join(sorted(merged)) + '\n'
    if not output.exists() or output.read_text() != content:
        temporary = output.with_suffix('.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(output)
    print(f'Collected {len(merged)} unique proxy links.')
    if failed:
        print(f'::warning::{failed} sources failed or contained no accepted links; published successful sources only.')


if __name__ == '__main__':
    try:
        collect(os.environ.pop('PROXY_SOURCES', ''))
    except Exception:
        print('::error::Collection failed; check Secret configuration and source availability. Previous output preserved.')
        sys.exit(1)
