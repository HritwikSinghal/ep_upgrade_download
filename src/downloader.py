import json
import os
import re

import requests

from src import ytdl_downloader, searx


def get_name_no_ext(filename: str):
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

        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Referer': 'www.sonyliv.com/',
            'Origin': 'www.sonyliv.com',
            'Host': 'www.sonyliv.com'
        }

    def __create_search_query(self, filename: str, prefix: str = '', suffix: str = ''):
        """
        Create search Query from filename
        :param filename: str : file name from which we extract ep no
        :param prefix: prefix for query
        :param suffix: suffix to attach at end of query
        :return: str: query
        """
        ep_name = get_name_no_ext(filename)

        return prefix + ' ' + ep_name + ' ' + suffix

    def __check_url(self, url: str, file_name: str):
        """
        checks if the url is correct for that episode
        :param url:
        :return: bool
        """
        if url == '':
            return False

        # parse url and check episode number
        # url = 'https://www.sonyliv.com/shows/taarak-mehta-ka-ooltah-chashmah-1700000084/daya-ka-surprise-1000021355'
        response = requests.get(url, headers=self._headers, allow_redirects=True)

        # Find ep no from url
        x = re.findall(r'\"episodeNumber\":\"(\d+)\"', response.text)
        try:
            # check if this matches the ep no we want to download
            ep_no = x[0]
            ep_name_we_want = re.findall('\d+', get_name_no_ext(file_name))[0]
            # ep_name_we_want = re.findall('\d{3,4}', get_name_no_ext(file_name))[0]

            if ep_no != ep_name_we_want:
                return False
        except:
            return False

        return True

    def __get_best_result(self, results: dict, file_name: str):
        """
        from all the results, get the best match
        :param results: dict: dict (from Searx) which contains data in json format
        :return: str: url of the best match result
        """
        for result in results['results']:
            if result['engines'][0] == 'google' and result['parsed_url'][1] == 'www.sonyliv.com':
                url = result['url']
                if self.__check_url(url, file_name):
                    # print(url)
                    return url

        ## ---- for Debug ---- ##
        os.chdir(self._save_dir)
        with open(file_name + '_error_debug.txt', 'w+') as ttt:
            json.dump(results, ttt, indent=2)
        ## ------------------- ##

        return ''

    def __download(self, url: str):
        """
        Start Download using YTDL class and save it save_dir
        :param url: url to be downloaded
        :return:
        """
        my_ytdl = ytdl_downloader.YTDL_Downloader()
        my_ytdl.set_save_dir(self._save_dir)
        my_ytdl.set_download_url(download_url=url)
        status_code: int = my_ytdl.start()
        return status_code

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

    ## ---------------------------------------------------------------------- ##

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

    ## ---------------------------------------------------------------------- ##

    def start(
            self,
            start_vid_no: int,
            skip_n: int,
            files_list: list[tuple],
            global_save_dir: str,
            search_prefix: str = '',
            search_suffix: str = ''
    ):

        self._save_dir = global_save_dir
        self._start_vid_no = start_vid_no

        # Todo : make it skip n files instead of doing first n.
        # Todo: handle case where files are not multiple of n
        for i in range(start_vid_no, start_vid_no + skip_n):
            file = files_list[i]

            # If file has been downloaded, skip this
            if file[2]:
                continue

            # Get results for each file
            search_query: str = self.__create_search_query(file[1], prefix=search_prefix, suffix=search_suffix)
            # print(search_query)
            results: dict = searx.SearX().get_results_json(search_query=search_query)
            url = self.__get_best_result(results, file_name=file[1])

            # Setup Youtube Downloader and start downloading
            status_code: int = self.__download(url)

            # Update tuple[2] to True, means file has successfully been downloaded
            if status_code == 1:
                files_list[i] = self.__update_tuple(file, 2)
