import json
import multiprocessing
import os
import re

from src import file_crawler
from src.downloader import downloader


def get_name_no_ext(filename):
    filename = re.sub(
        r'\.[mM][pP]4|'
        r'\.[mM][kK][vV]|'
        r'\.[wW][eE][bB][mM]',

        '',
        filename
    )
    return str(filename).strip()


class Upgrade_SL:

    def __init__(self, files_dir: str, exclude_dirs: dict = None, save_dir: str = ''):
        self.files_dir: str = files_dir
        self.exclude_dirs: dict = exclude_dirs
        self._save_dir: str = save_dir
        self._files: list = []

        self.__init_func()

    def __init_func(self):
        """
        This will call some methods on class initialization
        :return:
        """
        self.__set_save_dir()

    def __set_save_dir(self):
        """
        Sets 'self._save_dir', where downloaded files will be saved
        """

        if not self._save_dir:
            download_dir = os.path.expanduser("~/Downloads/Video")

            if not os.path.isdir(download_dir):
                os.mkdir(download_dir)
            self._save_dir = download_dir
        print("Save Dir: ", self._save_dir)

    def __update_file_list(self):
        """
        Add an extra bool field to each tuple of '_files' which is true when the download of that file in complete
        :return:
        """
        for i in range(len(self._files)):
            file = self._files[i]
            y = list(file)
            y.append(False)
            self._files[i] = tuple(y)

    def __pp_dict(self, json_dict: dict):
        print(json.dumps(json_dict, indent=4))

    def __parallel(self, search_prefix: str = '', search_suffix: str = ''):
        # Todo : make process pool and remove hardcoded values
        # creating processes
        n = 4  # from 0 to 4, 5 to 8, 9 to 12, 13 to 16 . All intervals are of size n
        p1 = multiprocessing.Process(
            target=downloader().start, args=(0, n, self._files, self._save_dir, search_prefix, search_suffix,)
        )
        p2 = multiprocessing.Process(
            target=downloader().start, args=(n, n, self._files, self._save_dir, search_prefix, search_suffix,)
        )
        p3 = multiprocessing.Process(
            target=downloader().start, args=(2 * n, n, self._files, self._save_dir, search_prefix, search_suffix,)
        )
        p4 = multiprocessing.Process(
            target=downloader().start, args=(3 * n, n, self._files, self._save_dir, search_prefix, search_suffix,)
        )

        # starting process
        p1.start()
        p2.start()
        p3.start()
        p4.start()

        # wait until process is finished
        p1.join()
        p2.join()
        p3.join()
        p4.join()

        # processes finished
        print("Done!")

    def start(self, search_prefix: str = '', search_suffix: str = ''):
        # Get files list
        my_crawler = file_crawler.File_Crawler(
            file_dir=self.files_dir,
            exclude_dirs=self.exclude_dirs,
            recursive_crawl_flag=True
        )
        self._files: list = my_crawler.get_files()

        # Add boolean flag to files which will be true when file is downloaded.
        self.__update_file_list()

        """
        self._files : list : List of files in that folder,
        stores a tuple = (absolute path of file's folder : str, name of file : str, downloaded: bool)
        """

        ## ---- for Debug ---- ##
        # downloader().start(0, 4, self._files, self._save_dir)
        ## ------------------- ##

        self.__parallel(search_prefix=search_prefix, search_suffix=search_suffix)
