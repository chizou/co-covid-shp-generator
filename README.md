This application connects to Google Drive to download the [Colorado COVID-19
case data](https://drive.google.com/drive/folders/1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1).
The application then processes the county specific data into the attribute table of a
Colorado by county shapefile

## Quick Start
```
git clone https://github.com/chizou/co-covid-shp-generator
 d co-covid-shp-generator
pip install  --upgrade -r requirements.txt
mkdir downloads
cp sample.csv downloads/
python ./final_project.py
```

## Configuration
### Google Drive Configuration
In order to use this application, you'll need to configure your Google credentials to download
data files from Google Drive
1. Configure your Google credentials based on [these instructions](https://support.google.com/googleapi/answer/6158862?hl=en)
2. Ensure the credentials are configured to allow _Google Drive API_. Implementing an IP based restriction is also recommended
3. set those credentials in the `config.yml` file with the following format:
```
google-drive-creds:
    your-api-key
```

### Operation
The application is meant to be repeatable such that subsequent runs will always return the same result as long as the data source doesn't change. The reasoning behind this is because the fast pace that the data is changing because our understanding of COVID is rapidly changing. Additionally, the State of Colorado continues to add additional data points as time progresses.

This application uses the base shapefile provided in the `shapefiles/base` directory to create derivative shapefiles from. Updates to the base shapefile will appear in all derivative shapefiles as well, with the limitation of the capabilities provided by pyshp

### Statistic Mapping
Due to the fact that ESRI Shapefile format only supports a max of 10 characters, the attribute table fields have been shortened. All statistics below are per county. Here is the mapping:

| Field name| Mapped Statistic|
|:---------:|:----------------:|
| CASECOUNT | Total number of cases per county|
| CASEPER100| Nubmer of cases per 100,000 people|
| DEATHS | Total number of deaths |
| PCR | Total number of PCR test conducted |
| SEROLOGY | Total number of serology tests conducted |
| TESTRATE | Rate of test per 100,000 people|
| TOTALTESTS| Total number of tests conducted |

## Contributing
### pre-commit
This repo usese pre-commit and requires python version 3.7. Since there are the potential for Google API secrets, we do use Yelp's detect-secrets which will need to be installed
