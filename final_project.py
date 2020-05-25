# My final final project!
# Adam Chou
# This application connects to Google Drive to download the Colorado COVID-19
# case data from https://drive.google.com/drive/folders/1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1.
# The application then processes the county specific data into the attribute table of a
# Colorado by county shapefile

from cocovidprocessor import gdrivedownloader as gd
import yaml

with open("config.yml") as configfh:
    try:
        config = yaml.safe_load(configfh)
        gdrive_creds = config['google-drive-creds']
    except yaml.YAMLError as e:
        print(f"Exiting... Error loading config: {e}")
        sys.exit()

downloader = gd.GDriveDownloader(api_key=gdrive_creds)
downloader.download()