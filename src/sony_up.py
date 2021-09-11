import json
import multiprocessing
import os
import re
import time
import traceback

from src import file_crawler
from src import searx
from src import ytdl_downloader


def get_name_no_ext(filename):
    filename = re.sub(
        r'\.[mM][pP]4|'
        r'\.[mM][kK][vV]|'
        r'\.[wW][eE][bB][mM]',

        '',
        filename
    )
    return str(filename).strip()


class parallel_downloader:

    def __init__(self):
        self._save_dir: str = ''
        self._start_vid_no: int = -1

    def __create_search_query(self, filename: str):
        ep_name = get_name_no_ext(filename)

        return 'Taarak Mehta Ka Ooltah Chashmah ' + ep_name + ' sonyliv'

    def __get_best_result(self, results: dict):
        for result in results:
            if result['engines'][0] == 'google' and result['parsed_url'][1] == 'www.sonyliv.com':
                url = result['url']
                # print(url)
                if url != '':
                    return url

        return ''

    def __create_folders(self, filename: str, old_save_dir):
        filename = get_name_no_ext(filename)
        download_dir = os.path.expanduser(old_save_dir + '/' + filename)

        if not os.path.isdir(download_dir):
            os.mkdir(download_dir)
        self._save_dir = download_dir

    def __download(self, url):
        my_ytdl = ytdl_downloader.YTDL_Downloader()
        os.chdir(self._save_dir)
        print("chdir to ", self._save_dir)

        my_ytdl.set_download_url(url)
        my_ytdl.start()

    def __rename_move(self, file, global_save_dir):
        os.chdir(self._save_dir)

        old_name: str = os.listdir(self._save_dir)[0]
        old_name_full: str = os.path.join(self._save_dir, os.listdir(self._save_dir)[0])
        new_name = os.path.join(global_save_dir, get_name_no_ext(file[1]) + ' - ' + old_name)

        # print('self._save_dir=', self._save_dir)
        # print('oldname= ', old_name)
        # print('old_name_full=', old_name_full)
        # print('newname= ', new_name)

        os.rename(old_name_full, new_name)

    def __update_tuple(self, tuple_name, pos):
        y = list(tuple_name)
        y[pos] = True
        tuple_name = tuple(y)
        return tuple_name

    def start(self, start_vid_no: int, files: list[tuple], global_save_dir):
        self._save_dir = global_save_dir
        self._start_vid_no = start_vid_no

        for i in range(start_vid_no, start_vid_no + 4):
            print()

            # create save directory for each file
            file = files[i]

            # If file has been downloaded, skip this
            if file[2]:
                continue

            self.__create_folders(file[1], global_save_dir)

            # Get results for each file
            search_query: str = self.__create_search_query(file[1])
            print(search_query)
            results: dict = searx.SearX().get_results_json(search_query=search_query)['results']
            url = self.__get_best_result(results)

            while not file[2]:
                try:
                    # Setup Youtube Downloader and start downloading
                    self.__download(url)

                    # Update tuple[2] to True, means file has successfully been downloaded
                    file = self.__update_tuple(file, 2)

                    # Download has finished, now rename file and move it to common location
                    # self.__rename_move(file, global_save_dir)

                except:
                    time.sleep(15)
                    traceback.print_exc()


class Upgrade_SL:

    def __init__(self, save_dir: str = ''):
        self.files_dir = '/Videos'
        self.exclude_dirs = {
            'ABC': '1',
            'XYZ': '0'
        }
        self._save_dir: str = save_dir
        self._files = []

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

    def __pp_dict(self, json_dict: dict):
        print(json.dumps(json_dict, indent=4))

    def __parallel(self):
        # creating processes
        p1 = multiprocessing.Process(target=parallel_downloader().start, args=(0, self._files, self._save_dir,))
        p2 = multiprocessing.Process(target=parallel_downloader().start, args=(4, self._files, self._save_dir,))
        p3 = multiprocessing.Process(target=parallel_downloader().start, args=(8, self._files, self._save_dir,))
        p4 = multiprocessing.Process(target=parallel_downloader().start, args=(12, self._files, self._save_dir,))

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

    def start(self):
        # Get files list
        my_crawler = file_crawler.File_Crawler(file_dir=self.files_dir, exclude_dirs=self.exclude_dirs,
                                               recursive_crawl_flag=True)
        self._files = my_crawler.get_files()

        """
        self._files : list : List of files in that folder,
        stores a tuple = (absolute path of file's folder : str, name of file : str, downloaded: bool)
        """

        self.__parallel()
