"""Run exactly one ten-cell sample, then serve the saved result without a key."""
import argparse
import json
import os
from pathlib import Path
import sys
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import Handler, ROOT, load_env
from design_preview import DesignPreview, SavedPreview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true', help='Explicitly authorize one request containing ten decisions')
    parser.add_argument('--port', type=int, default=8012)
    parser.add_argument('--directory', default=str(ROOT / 'recordings/private/design-preview-10'))
    args = parser.parse_args()
    directory = Path(args.directory)
    if args.run:
        load_env()
        preview = DesignPreview(directory, count=10)
        try:
            preview.dispatch('/api/step', {})
        finally:
            print(json.dumps(dict(status=preview.preview['status'],
                                  decisions=len(preview.sim.decisions), usage=preview.jev.status())), flush=True)
    saved = SavedPreview(directory / 'preview.json')
    if args.run:
        del preview
    os.environ.pop('TYPESAFE_API_KEY', None)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.studio = saved
    print(f'LN design preview: http://127.0.0.1:{args.port} (read-only; no new API calls)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
