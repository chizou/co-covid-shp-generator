# My final final project!
# Adam Chou
# This application connects to Google Drive to download the Colorado COVID-19
# case data from https://drive.google.com/drive/folders/1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1.
# The application then processes the county specific data into the attribute table of a
# Colorado by county shapefile

from cocovidprocessor import downloader
from cocovidprocessor import processor
import yaml
import sys

def load_configs():
    with open("config.yml") as configfh:
        try:
            return yaml.safe_load(configfh)
        except yaml.YAMLError as e:
            print(f"Exiting... Error loading config: {e}")
            sys.exit()


def main():
    configs = load_configs()
    gdrive_creds = configs['google-drive-creds']

    # First, download the csv files using our downloader class
    download = downloader.Downloader(api_key=gdrive_creds)
    download.download()

    # Once we have the files, process them
    process = processor.CsvProcessor(base_shapefile='shapefiles/base/COUNITES.shp')
    process.process_csvs()


if __name__ == "__main__":
    main()


