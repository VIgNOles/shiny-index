"""Compare every staged Pages file with an anonymous public URL."""
import argparse
import hashlib
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.check_site import check


def verify_public(site, base_url):
    site = Path(site)
    check(site)
    parsed = urlsplit(base_url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError('public URL must be an HTTPS directory URL without query or fragment')
    prefix = base_url.rstrip('/') + '/'
    files = sorted(p for p in site.rglob('*') if p.is_file())
    for path in files:
        relative = path.relative_to(site).as_posix()
        url = prefix + quote(relative, safe='/')
        request = Request(url, headers={'User-Agent': 'shiny-index-public-check/1',
                                        'Cache-Control': 'no-cache'})
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise ValueError(f'HTTP {response.status}: {relative}')
            remote = response.read()
        expected = path.read_bytes()
        if hashlib.sha256(remote).digest() != hashlib.sha256(expected).digest():
            raise ValueError(f'public bytes differ: {relative}')
    return {'files': len(files), 'public_url': prefix, 'matches': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site')
    parser.add_argument('public_url')
    args = parser.parse_args()
    print(verify_public(args.site, args.public_url))


if __name__ == '__main__':
    main()
