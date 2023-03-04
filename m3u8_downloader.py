import os
import requests
import subprocess
from urllib.parse import urlparse
from uuid import uuid4


class M3u8Downloader:

    def __init__(self, url: str):
        self.headers: dict = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        self.m3u8_url: str = url

    def get_all_playlists(self) -> dict:
        response = requests.get(self.m3u8_url, headers=self.headers)
        assert response.ok, f'Can\'t get playlists {response.text}'

        strings = response.text.split('\n')
        playlists = {}
        while (i := 0) < len(strings):
            if strings[i].startswith('#EXT-X-STREAM-INF'):
                resolution = strings[i].split('=')[-1]
                playlists[resolution] = strings[i + 1]
                i += 2
            else:
                i += 1

        return playlists

    @staticmethod
    def choose_playlist_url(playlists: dict, resolution: int = None) -> str:
        return playlists[resolution] if resolution else next(iter(playlists.values()))

    def get_ts_urls(self, playlist_url: str) -> list:
        parsed_uri = urlparse(playlist_url)
        host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

        response = requests.get(playlist_url, headers=self.headers)
        assert response.ok, f'Can\'t get ts urls {response.text}'

        ts_urls = [(host + url).strip() for url in response.text.strip('\n') if url.endswith('.ts')]
        return ts_urls

    def make_ts_file(self, ts_urls: list) -> str:
        output_filename = f'file_{uuid4()}.ts'
        with open(output_filename, 'wb') as file:
            for each in ts_urls:
                content = requests.request("GET", each, headers=self.headers, stream=True).content
                file.write(content)
        return output_filename

    @staticmethod
    def make_mp4_from_ts(ts_file_name: str):
        subprocess.run(['ffmpeg', '-i', ts_file_name, f'{ts_file_name.split(".")[0]}.mp4'])

    def m3u8_or_ts(self):
        response = requests.get(self.m3u8_url, headers=self.headers)
        assert response.ok, f'Can\t get response {response.text}'

        return 'm3u8' if '#EXT-X-STREAM-INF' in response.text else 'ts'

    def from_m3u8_to_mp4(self, resolution: str = None):
        content_format = self.m3u8_or_ts()
        if content_format == 'm3u8':
            playlists = self.get_all_playlists()
            playlist_url = self.choose_playlist_url(playlists, resolution)
        else:
            playlist_url = self.m3u8_url

        ts_urls = self.get_ts_urls(playlist_url)
        ts_file_name = self.make_ts_file(ts_urls)
        self.make_mp4_from_ts(ts_file_name)
        os.remove(ts_file_name)


if __name__ == "__main__":
    m3u8_url = input('Enter m3u8 url: ')
    m3u8_downloader = M3u8Downloader(m3u8_url)
    if m3u8_downloader.m3u8_or_ts() == 'm3u8':
        pls = m3u8_downloader.get_all_playlists()

        print('Choose an resolution: ')
        for i, option in enumerate(pls.keys()):
            print(f'{i + 1}. {option}')
        while True:
            resolution = input('Enter the number of your choice: ')
            if resolution.isdigit() and int(resolution) in range(1, len(pls.keys()) + 1):
                break
            else:
                print('Invalid choice. Please try again.')

        playlist_url = m3u8_downloader.choose_playlist_url(pls, int(resolution))
    else:
        playlist_url = m3u8_url

    ts_urls = m3u8_downloader.get_ts_urls(playlist_url)
    ts_file_name = m3u8_downloader.make_ts_file(ts_urls)
    m3u8_downloader.make_mp4_from_ts(ts_file_name)
    os.remove(ts_file_name)
