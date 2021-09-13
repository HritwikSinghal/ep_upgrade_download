import json
import os
import re
from concurrent.futures import ProcessPoolExecutor

import requests

from src import file_crawler
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


class _Parallel_Downloader:
    def __init__(self, save_dir):
        self._save_dir = save_dir

    def download(self, url: str):
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


class Downloader:
    """
    Search query on searX and download from website automatically using yt-dl
    takes files_list (list) which contains file name (str) and creates search query using prefix and suffix as supplied
    Can download multiple files.
    """

    def __init__(self, files_dir: str, exclude_dirs: dict = None, save_dir: str = ''):
        """
        :param files_dir: str : dir where files are stored
        :param exclude_dirs: dict : earch entry will contain dir to be excluded as key and a bool as value
                                    if skip dir and its sub-dir, then -> True,
                                    else if only skip that dir -> false
        :param save_dir: str: optional, folder where media is to be saved (absolute path)
        """

        self._files_dir: str = files_dir
        self._exclude_dirs: dict = exclude_dirs
        self._save_dir: str = save_dir

        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Referer': 'www.sonyliv.com/',
            'Origin': 'www.sonyliv.com',
            'Host': 'www.sonyliv.com'
        }

        self._search_prefix = ''
        self._search_suffix = 'site:www.sonyliv.com'

        self.__init_func()

    def __init_func(self):
        """
        This will call some methods on class initialization
        :return:
        """
        self.__set_save_dir()

    def get_save_dir(self):
        return self._save_dir

    def set_save_dir(self, save_dir):
        self._save_dir = save_dir

    def __set_save_dir(self):
        """
        Sets 'self._save_dir', where downloaded files will be saved
        """
        if not self._save_dir:
            self.set_save_dir(os.path.expanduser("~/Downloads/Video"))
        if not os.path.isdir(self.get_save_dir()):
            os.mkdir(self.get_save_dir())

        print("Save Dir: ", self.get_save_dir())

    # ------------------------- #

    def __create_search_query(self, filename: str, prefix: str = '', suffix: str = ''):
        """
        Create search Query from filename
        :param filename: str : file name from which we extract ep no
        :param prefix: prefix for query
        :param suffix: suffix to attach at end of query
        :return: str: query
        """
        ep_name = get_name_no_ext(filename)

        return str(prefix + ' ' + ep_name + ' ' + suffix).strip()

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

        # Find ep no from url, this regex is specific to sonyliv
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
        :param results: dict: dict (from SearX) which contains data in json format
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

    def __create_file_tuple_list(self, files_list: list):
        """
        For each file:- separate parent folder, file name and extension,
        add a download field as bool will be true when the download of that file in complete.
        Return as a list of tuples
        :return: list = (path to file, file name, extension, bool)
        """

        final_list = []

        for file in files_list:
            # Check if file_name contain full path or only name

            # Add download field

            # Extract filename
            filename = str(file).split('/')[-1]

            # Extract extension
            file_ext = str(filename).split('.')[-1]
            filename = str(filename).rsplit('.', 1)[0]

            # Extract parent folder
            file_dir = str(file).rsplit('/', 1)[0]

            # and add bool field
            y = [file_dir, filename, file_ext, False]

            # Convert to tuple
            final_list.append(tuple(y))

        return final_list

    def __get_files_list(self):
        my_crawler = file_crawler.File_Crawler(
            file_dir=self._files_dir,
            exclude_dirs=self._exclude_dirs,
            recursive_crawl_flag=True
        )
        """
        files_list: list: list of file name (str) (may contain absolute file path)
        """
        files: list = my_crawler.get_files()

        ## ---- for Debug ---- ##
        # for x in self._files:
        #     print(x)
        # input()
        ## ------------------- ##

        # To separate parent folder, file name and extension. Also add a download field. Return as tuple
        file_tuple_list = self.__create_file_tuple_list(files)

        return file_tuple_list

    # ------------------------- #

    def _get_url_and_download(self, filename):
        # Create search query for each file
        search_query: str = self.__create_search_query(filename=filename,
                                                       prefix=self._search_prefix,
                                                       suffix=self._search_suffix)

        # Get results for that search query from searX
        results: dict = searx.SearX().get_results_json(search_query=search_query)

        # from all results, find best result and Extract it's url
        url = self.__get_best_result(results, file_name=filename)

        # Create download object And download!
        my_p_d = _Parallel_Downloader(self._save_dir)
        my_p_d.download(url)

    def start(self, search_prefix, search_suffix):
        """
        Get files list from filecrawler, create search query for each file and download.

        :param search_prefix: str: prefix req for search query
        :param search_suffix: str: suffix req for search query
        :return: None
        """

        self._search_prefix = search_prefix
        self._search_suffix = search_suffix

        """
        file_tuple_list = list of (path to file, file name, extension, bool)
        """
        file_tuple_list = self.__get_files_list()

        file_name_list = [x[1] for x in file_tuple_list]

        # Todo : parallel here
        # creating processes pool
        with ProcessPoolExecutor(max_workers=4) as executor:
            executor.map(self._get_url_and_download, file_name_list)

        # processes finished
        print("Done!")
