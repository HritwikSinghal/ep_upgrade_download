from src.sony_downloader import Downloader

if __name__ == '__main__':
    files_dir = '/run/media/'
    exclude_dirs = {
        'AAA': '1',
        'AEE': '0',
        'OEOE': '1',
        '>U>U>': '1'
    }
    search_prefix = 'AAA'
    search_suffix = 'BBB'

    my_downloader = Downloader(files_dir=files_dir, exclude_dirs=exclude_dirs)
    my_downloader.start(search_prefix=search_prefix, search_suffix=search_suffix)
