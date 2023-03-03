import os
import requests
import subprocess
from urllib.parse import urlparse

I = 3

HEADERS = {

    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}


def get_all_playlists(url) -> dict:
    body_text = requests.request("GET", url, headers=HEADERS).text
    strings: list = body_text.split('\n')
    i: int = 0
    playlists: dict = dict()
    while i < len(strings):
        if strings[i].startswith('#EXT-X-STREAM-INF'):
            playlists[strings[i].split('=')[-1]] = strings[i + 1]
            i += 2
        else:
            i += 1

    return playlists


def get_ts_urls(playlists: dict, resolution: str = '720p') -> list:
    playlist_url = playlists[resolution]
    parsed_uri = urlparse(playlist_url)
    host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    body_text = requests.request("GET", playlist_url, headers=HEADERS).text
    strings: list = body_text.split('\n')

    ts_urls = [(host + url).strip() for url in strings if url.endswith('.ts')]
    return ts_urls


def make_video_file(ts_urls: list):
    global I
    i = len(ts_urls)
    with open(f'file{I}', 'wb') as file:
        for each in ts_urls:
            content = requests.request("GET", each, headers=HEADERS, stream=True).content
            file.write(content)
            i -= 1
            print(i)

    subprocess.run(['ffmpeg', '-i', f'file{I}', f'{I}.mp4'])
    os.remove(f'file{I}')
    I += 1


pls = [

]
for each in pls:
    playlists = get_all_playlists(each)
    ts_urls_ = get_ts_urls(playlists)
    make_video_file(ts_urls_)
