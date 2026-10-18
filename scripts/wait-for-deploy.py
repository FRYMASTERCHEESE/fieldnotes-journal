"""Ensure live browser checks run against this workflow's deployed revision."""
import os, time, json
from urllib.request import urlopen
expected = os.environ['GITHUB_SHA']
for attempt in range(60):
    try:
        with urlopen('https://frymastercheese.github.io/fieldnotes-journal/version.json?revision='+expected, timeout=15) as response:
            if json.load(response)['revision'] == expected:
                print('Verified live revision:',expected)
                break
    except Exception as error:
        print('Waiting for deployment:',type(error).__name__)
    time.sleep(3)
else:
    raise SystemExit('The expected revision did not become live.')
