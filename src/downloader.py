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


# ## ---------------------------------------------------------------------- ##
#
# def __create_folders(self, filename: str, old_save_dir):
#     """
#     Will create a folder for each filename at old_save_dir
#     :param filename: str:  Name of file (ep number)
#     :param old_save_dir: where folder is to be created
#     :return:
#     """
#     filename = get_name_no_ext(filename)
#     download_dir = os.path.expanduser(old_save_dir + '/' + filename)
#
#     if not os.path.isdir(download_dir):
#         os.mkdir(download_dir)
#     self._save_dir = download_dir
#
# def __rename_move(self, file: tuple, global_save_dir: str):
#     """
#     check if file has been downloaded, then rename and move it accordingly
#     :param file: tuple:
#     :param global_save_dir: str
#     :return:
#     """
#
#     # old_todo: check if file has been downloaded
#     os.chdir(self._save_dir)
#
#     old_name: str = os.listdir(self._save_dir)[0]
#     old_name_full: str = os.path.join(self._save_dir, os.listdir(self._save_dir)[0])
#     new_name = os.path.join(global_save_dir, get_name_no_ext(file[1]) + ' - ' + old_name)
#
#     # print('self._save_dir=', self._save_dir)
#     # print('oldname= ', old_name)
#     # print('old_name_full=', old_name_full)
#     # print('newname= ', new_name)
#
#     os.rename(old_name_full, new_name)
#
# ## ---------------------------------------------------------------------- ##


class downloader:
    """
    Search query on searX and download from website automatically using yt-dl
    takes files_list (list) which contains file name (str) and creates search query using prefix and suffix as supplied
    Can download multiple files.
    """

    def __init__(self, save_dir: str = '', preferred_engine: str = '', preferred_website: str = ''):
        """
        :param save_dir: str: optional, folder where media is to be saved (absolute path)
        :param preferred_engine: str: preferred search engine to filter search results
        :param preferred_website: str : preferred website to search results
        """

        self._save_dir: str = save_dir
        self._preferred_engine: str = preferred_engine
        self._preferred_website: str = preferred_website

        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Referer': 'www.sonyliv.com/',
            'Origin': 'www.sonyliv.com',
            'Host': 'www.sonyliv.com'
        }

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

        print("YT-DL Save Dir: ", self.get_save_dir())

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

    # Todo: remove hard code
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

        # Todo : Remove sonyliv and google hardcode.
        #        replace 'google' with 'self._preferred_engine' and 'www.sonyliv.com' with 'self._preferred_website'
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
        my_ytdl.set_save_dir(self.get_save_dir())
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

    def __create_file_tuple_list(self, files_list: list):
        """
        For each file:- separate parent folder, file name and extension,
        add a download field as bool will be true when the download of that file in complete.
        Return as a list of tuples
        :return: list = (path of file, file name, extension, bool)
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

    def download(self, files_list: list, search_prefix: str = '', search_suffix: str = ''):
        """
        :param files_list: list: list of file name (str) (may contain absolute file path)
        :param search_prefix: str: prefix req for search query
        :param search_suffix: str: suffix req for search query
        :return: None
        """

        # To separate parent folder, file name and extension. Also add a download field. Return as tuple
        file_tuple_list = self.__create_file_tuple_list(files_list)

        for i in range(len(file_tuple_list)):
            file_tuple = file_tuple_list[i]

            # Get search query for each file
            filename = file_tuple[1]
            search_query: str = self.__create_search_query(filename=filename,
                                                           prefix=search_prefix,
                                                           suffix=search_suffix)

            # Get results for that search query from searX
            results: dict = searx.SearX().get_results_json(search_query=search_query)

            # from all results, find best result and Extract it's url
            url = self.__get_best_result(results, file_name=file_tuple[1])

            # if the file is not downloaded or if we could not find best result
            # Todo: maybe update the 'url' condition
            if not file_tuple[3] and url != '':
                # Setup Youtube Downloader and start downloading
                status_code: int = self.__download(url)

                # Update tuple[3] to True, means file has successfully been downloaded
                if status_code == 1:
                    file_tuple_list[i] = self.__update_tuple(file_tuple, pos=3)
