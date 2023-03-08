import os
import re
import requests
import subprocess
from urllib.parse import urlparse
from uuid import uuid4


class M3u8Downloader:

    def __init__(self, url: str):
        self.headers: dict = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }
        self.m3u8_url: str = url

    @staticmethod
    def make_url(url: str, base_url):
        if url.startswith('http'):
            return url.strip()

        parsed_base_url = urlparse(base_url)
        count_slash = url.count('/') + 1
        result = f"{parsed_base_url.scheme}://{parsed_base_url.hostname}" \
                 f"{'/'.join(parsed_base_url.path.split('/')[:-count_slash])}/{url}"
        return result

    def get_all_playlists_urls(self) -> dict:
        response = requests.get(self.m3u8_url, headers=self.headers)
        assert response.ok, f'Can\'t get playlists {response.text}'

        strings = response.text.split('\n')
        playlists = {}
        i = 0
        while i < len(strings):
            if strings[i].startswith('#EXT-X-STREAM-INF'):
                resolution = re.findall(r'RESOLUTION=(\d*x\d*)', strings[i])[0]
                playlists[resolution] = self.make_url(strings[i + 1], self.m3u8_url)
                i += 2
            else:
                i += 1

        return playlists

    @staticmethod
    def choose_playlist_url(playlists: dict, resolution: int = None) -> str:
        return playlists[resolution] if resolution else next(iter(playlists.values()))

    def get_ts_urls(self, playlist_url: str) -> list:
        response = requests.get(playlist_url, headers=self.headers)
        assert response.ok, f'Can\'t get ts urls {response.text}'
        ts_urls = [self.make_url(url, playlist_url) for url in response.text.split('\n') if url.endswith('.ts')]
        return ts_urls

    def make_ts_file(self, ts_urls: list) -> str:
        output_filename = f'file_{uuid4()}.ts'
        with open(output_filename, 'wb') as file:
            print(f'Downloading ts files')
            for i, each in enumerate(ts_urls):
                content = requests.request("GET", each, headers=self.headers, stream=True).content
                file.write(content)
            print(f'Finish downloading ts files')
        return output_filename

    @staticmethod
    def make_mp4_from_ts(ts_file_name: str):
        print('Start make video')
        subprocess.run(['ffmpeg', '-i', ts_file_name, f'{ts_file_name.split(".")[0]}.mp4'])
        print('Finish make video')

    def m3u8_or_ts(self):
        response = requests.get(self.m3u8_url, headers=self.headers)
        assert response.ok, f'Can\t get response {response.text}'

        return 'm3u8' if '#EXT-X-STREAM-INF' in response.text else 'ts'

    def from_m3u8_to_mp4(self, resolution: str = None):
        content_format = self.m3u8_or_ts()
        if content_format == 'm3u8':
            playlists = self.get_all_playlists_urls()
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
        pls = m3u8_downloader.get_all_playlists_urls()

        print('Choose an resolution: ')
        for i, option in enumerate(pls.keys()):
            print(f'{i + 1}. {option}')
        while True:
            resolution = input('Enter the number of your choice: ')
            if resolution.isdigit() and int(resolution) in range(1, len(pls.keys()) + 1):
                break
            else:
                print('Invalid choice. Please try again.')

        playlist_url = m3u8_downloader.choose_playlist_url(pls, list(pls.keys())[int(resolution) - 1])
    else:
        playlist_url = m3u8_url

    ts_urls = m3u8_downloader.get_ts_urls(playlist_url)
    ts_file_name = m3u8_downloader.make_ts_file(ts_urls)
    m3u8_downloader.make_mp4_from_ts(ts_file_name)
    os.remove(ts_file_name)
