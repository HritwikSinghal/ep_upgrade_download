import os
import re
import time
import traceback

from src import ytdl_downloader, searx


def get_name_no_ext(filename):
    filename = re.sub(
        r'\.[mM][pP]4|'
        r'\.[mM][kK][vV]|'
        r'\.[wW][eE][bB][mM]',

        '',
        filename
    )
    return str(filename).strip()


class downloader:

    def __init__(self):
        self._save_dir: str = ''
        self._start_vid_no: int = -1

    def __create_search_query(self, filename: str):
        """
        Create search Query from filename
        :param filename: str
        :return: str
        """
        ep_name = get_name_no_ext(filename)

        return 'Taarak Mehta Ka Ooltah Chashmah ' + ep_name + ' sonyliv'

    def __check_url(self, url: str):
        """
        checks if the url is correct for that episode
        :param url:
        :return: bool
        """
        if url == '':
            return False

        # todo : parse url and check episode number


        return True

    def __get_best_result(self, results: dict):
        """
        from all the results, get the best match
        :param results: dict: dict (from Searx) which contains data in json format
        :return: str: url of the best match result
        """
        for result in results:
            if result['engines'][0] == 'google' and result['parsed_url'][1] == 'www.sonyliv.com':
                url = result['url']
                if self.__check_url(url):
                    # print(url)
                    return url

        return ''

    def __download(self, url: str):
        """
        Start Download using YTDL class and save it save_dir
        :param url: url to be downloaded
        :return:
        """
        my_ytdl = ytdl_downloader.YTDL_Downloader()
        os.chdir(self._save_dir)
        print("chdir to ", self._save_dir)

        my_ytdl.set_download_url(url)
        my_ytdl.start()

    def __update_tuple(self, tuple_name: tuple, pos: int):
        """
        Update the tuple's flag at position 'pos' to True (when download has completed)
        :param tuple_name: tuple: tuple to be changed
        :param pos: int: position at which change occurs
        :return:
        """
        y = list(tuple_name)
        y[pos] = True
        tuple_name = tuple(y)
        return tuple_name

    def __create_folders(self, filename: str, old_save_dir):
        """
        Will create a folder for each filename at old_save_dir
        :param filename: str:  Name of file (ep number)
        :param old_save_dir: where folder is to be created
        :return:
        """
        filename = get_name_no_ext(filename)
        download_dir = os.path.expanduser(old_save_dir + '/' + filename)

        if not os.path.isdir(download_dir):
            os.mkdir(download_dir)
        self._save_dir = download_dir

    def __rename_move(self, file: tuple, global_save_dir: str):
        """
        check if file has been downloaded, then rename and move it accordingly
        :param file: tuple:
        :param global_save_dir: str
        :return:
        """

        # todo: check if file has been downloaded
        os.chdir(self._save_dir)

        old_name: str = os.listdir(self._save_dir)[0]
        old_name_full: str = os.path.join(self._save_dir, os.listdir(self._save_dir)[0])
        new_name = os.path.join(global_save_dir, get_name_no_ext(file[1]) + ' - ' + old_name)

        # print('self._save_dir=', self._save_dir)
        # print('oldname= ', old_name)
        # print('old_name_full=', old_name_full)
        # print('newname= ', new_name)

        os.rename(old_name_full, new_name)

    def start(self, start_vid_no: int, files_list: list[tuple], global_save_dir: str):
        self._save_dir = global_save_dir
        self._start_vid_no = start_vid_no

        for i in range(start_vid_no, start_vid_no + 4):
            print()
            file = files_list[i]

            # If file has been downloaded, skip this
            if file[2]:
                continue

            # create save directory for each file, Not needed after adding episode_number in YTDL 'outtmpl'
            # self.__create_folders(file[1], global_save_dir)

            # Get results for each file
            search_query: str = self.__create_search_query(file[1])
            # print(search_query)
            results: dict = searx.SearX().get_results_json(search_query=search_query)['results']
            url = self.__get_best_result(results)

            while not file[2]:
                try:
                    # Setup Youtube Downloader and start downloading
                    self.__download(url)

                    # Update tuple[2] to True, means file has successfully been downloaded
                    file = self.__update_tuple(file, 2)

                    # Download has finished, now rename file and move it to common location
                    # Not needed  after adding episode_number in YTDL 'outtmpl'
                    # self.__rename_move(file, global_save_dir)

                except:
                    time.sleep(15)
                    traceback.print_exc()
