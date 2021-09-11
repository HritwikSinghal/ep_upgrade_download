import os

import youtube_dl


class YTDL_Downloader:

    def __init__(self, prefix='', download_url='https://www.youtube.com/watch?v=VdyBtGaspss'):
        self._download_url: str = 'https://www.youtube.com/watch?v=4yVnnH4amd8'
        self._prefix = prefix
        self._ydl_opts: dict = {
            'progress_hooks': [self.__my_hook],
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '%(title)s.%(ext)s'
        }

    def __my_hook(self, d):
        if d['status'] == 'finished':
            file_tuple = os.path.split(os.path.abspath(d['filename']))
            print("Done downloading {}".format(file_tuple[1]))
        if d['status'] == 'downloading':
            print(d['filename'], d['_percent_str'], d['_eta_str'])

    def set_prefix(self, prefix):
        self._prefix = prefix

    def get_prefix(self):
        return self._prefix

    def set_download_url(self, download_url):
        self._download_url = download_url

    def get_download_url(self):
        return self._download_url

    def start(self):
        with youtube_dl.YoutubeDL(self._ydl_opts) as ydl:
            ydl.download([self._download_url])
