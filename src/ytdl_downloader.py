import os
import time
import traceback

import youtube_dl


class YTDL_Downloader:
    """
    Inputs url as str, Downloads the video/audio to download dir
    Returns a code:
            1 = Successfull
            0 = wrong parameter
            -1/None = error
    """

    def __init__(self, download_url='https://www.youtube.com/watch?v=VdyBtGaspss', prefix=''):
        self._download_url: str = download_url
        self._prefix = prefix
        self._save_dir = os.path.expanduser("~/Downloads/Video")
        self._ydl_opts: dict = {
            'progress_hooks': [self.__my_hook],
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '%(episode_number)s - %(title)s.%(ext)s'
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

    def set_save_dir(self, save_dir):
        self._save_dir = save_dir

    def get_save_dir(self):
        return self._save_dir

    def start(self):
        os.chdir(self._save_dir)
        print("Saving to ", self._save_dir)

        if self._download_url == '':
            return 0  # means something is wrong with your params

        while True:
            try:
                with youtube_dl.YoutubeDL(self._ydl_opts) as ydl:
                    ydl.download([self._download_url])
            except:
                time.sleep(15)
                traceback.print_exc()
            else:
                return 1
