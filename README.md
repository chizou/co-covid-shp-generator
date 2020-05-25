This application connects to Google Drive to download the [Colorado COVID-19
case data](https://drive.google.com/drive/folders/1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1).
The application then processes the county specific data into the attribute table of a
Colorado by county shapefile

## Configuration
### Google Drive Configuration
In order to use this application, you'll need to configure your Google credentials to download
data files from Google Drive
1. Configure your Google credentials based on [these instructions](https://support.google.com/googleapi/answer/6158862?hl=en)
2. Ensure the credentials are configured to allow _Google Drive API_. Implementing an IP based restriction is also recommended
3. set those credentials in 