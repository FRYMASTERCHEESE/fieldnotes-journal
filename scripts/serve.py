"""Preview production project URLs without editing site configuration."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/fieldnotes-journal/'):
            self.path = self.path[len('/fieldnotes-journal'):]
        super().do_GET()

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1] / 'dist'
    print('Preview: http://127.0.0.1:8000/fieldnotes-journal/', flush=True)
    ThreadingHTTPServer(('127.0.0.1',8000),partial(Handler,directory=str(root))).serve_forever()
