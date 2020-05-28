import pandas as pd
import math
import os
import re
import shapefile
from collections import defaultdict
from shutil import copyfile
from glob import glob

import pprint

# This class handles ingestion of the CSV data files, associating them with
# the appropriate attribute table in the shapefile, and then writing the output shapefile
class CsvProcessor:
    def __init__(self, base_shapefile, data_dir='downloads', output_dir='shapefiles', output_file=None):
        self._data_dir = data_dir
        self._base_shapefile = base_shapefile
        self._output_dir = output_dir
        # if an output_file name isn't specified, just assume the same name as the input
        self._output_file = output_file if None else re.split("\/|\\\\", base_shapefile)[-1]

        # This list contains the definitions for the new attribute table fields
        self.__new_field_defs=[
            [ "CASECOUNT", "N", 10, 0 ],
            [ "TOTALTESTS", "N", 20, 0 ],
            [ "SEROLOGY", "N", 7, 2 ],
            [ "PCR", "N", 7, 2 ],
            [ "CASEPER100", "N", 7, 2 ],
            [ "DEATHS", "N", 7, 0 ],
            [ "TESTRATE", "N", 7, 2 ],
        ]
        self.__loaded_base_shape = None

    # Processes a single CSV file as specified with the file parameter. The CSV
    # file expects to be in the format provided by the State of Colorado's COVID study
    # Output is in the format: { County: { STAT1: Value1, STAT2: Value2, ... }, ...}
    def ingest_single_csv(self, file):
        # Sometimes, the state uploads empty files if it's the day immediately after
        try:
            file_contents = pd.read_csv(file)
        except pd.errors.EmptyDataError as e:
            print(f"File {file} doesn't contain any contents: {e}")
            return None

        stat_list = defaultdict(dict)
        for __, row in file_contents.iterrows():
            # Skip the following types of rows:
            # 1. Rows that contain state level data
            # 2. Rows that contain notes
            if (not re.search(r".*by County$", row['description']) or
                row['attribute'] == "Note"):
                continue

            # filter out all these extraneous words from our description
            statistic = re.sub('in Colorado|by County|Colorado|Total|Per [10,]+ People', '', row['description']).strip()

            # Since there is a 10 char limit in attribute tables, we need to create a mapping
            # to shorten all these names. This mapping needs to directly correlate with
            # with the dict in self.__fields_defs
            if statistic == "Case Counts":
                att_name = "CASECOUNT"
            # This specific statstic is broken down into sub categories
            elif statistic == 'COVID-19 Tests Performed':
                if row['metric'] == "Total Tests Performed":
                    att_name = "TOTALTESTS"
                elif "Serology" in row['metric']:
                    att_name = "SEROLOGY"
                elif "PCR" in row['metric']:
                    att_name = "PCR"
                else:
                    # If we ever detect a new COVID-19 test type, we should notify
                    # us so that we can add it
                    print(f"New COVID-19 Test detected: {row['metric']}")
                    continue
            elif statistic == "Case Rates":
                att_name = "CASEPER100"
            elif statistic == "Number of Deaths":
                att_name = "DEATHS"
            elif statistic == "Testing Rate":
                att_name = "TESTRATE"
            else:
                print(f"New statistic detected: {statistic}")
                continue

            # Some of the county names include the word "County", so let's remove it
            county = row['attribute'].replace(" County", "")
            # some cells have nan, so set to 0
            stat_list[county][att_name] = 0 if math.isnan(row['value']) else row['value']

        return stat_list


    # updates the base shapefile that's been ingested by load_shape and merges it with the csv
    # file that's been ingested by ingest_single_csv so that the file can be written
    # with save_shape()
    def update_county_shapefile(self, county_metrics):
        if self.__loaded_base_shape is None:
            raise Exception("base shape file hasn't been loaded yet.")

        # we first need define what all the new fields are before we can populate with values
        fields = self.__loaded_base_shape['fields'] + self.__new_field_defs

        # one important thing to note is that adding values must be in the exact some order as is defined in fields.
        # Construct this list to set the order
        new_field_order = [ x[0] for x in self.__new_field_defs ]
        shaperecs = self.__loaded_base_shape['shaperecs']
        for county, stats in county_metrics.items():
            new_values = []
            # For each county, assemble the new values based on new_field_order
            for field in new_field_order:
                try:
                    new_values.append(stats[field])
                except KeyError:
                    # Not all counties have a metric, so set to 0
                    new_values.append(0)
            try:
                shaperecs[county.upper()]['record'] = shaperecs[county.upper()]['record'] + new_values
            except KeyError:
                # Some dummy values are in the counties field, e.g. UNKNOWN
                continue

        merged_shapefile = {
            "fields": fields,
            "shaperecs": shaperecs,
        }
        print(merged_shapefile)
        return merged_shapefile


    # Iterate through all the downloaded files and create an updated shapefile for each
    # csv by date
    def process_csvs(self):
        file_list = glob(f"{self._data_dir}/*05-23.csv")
        for file in file_list:
            county_metrics = self.ingest_single_csv(file)
            merged_file = self.update_county_shapefile(county_metrics)
            self._save_shape(merged_file)


    # Load the contents of the shapefile into a dict as follows:
    # fields - contains the pyshp formatted list of fields
    # shape - an dict of dicts that contains every row in the existing shapefile. We
    #         key off the name of the column to make updating existing counties easier
    def _load_shape(self):
        shaperecs = {}
        with shapefile.Reader(self._base_shapefile) as shp:
            fields = shp.fields[1:]
            for shaperec in shp.iterShapeRecords():
                shaperecs[shaperec.record[0]] = {
                    "record": shaperec.record,
                    "shape": shaperec.shape
                }

        self.__loaded_base_shape = {
            "fields" : fields,
            "shaperecs": shaperecs,
        }


    # takes a dict as defined in _load_shape() and saves that into a shapefile. We
    # allow an optional output_path specification in case we're trying to create other
    # shapefiles
    def _save_shape(self, shape, output_path=None):
        if output_path is None:
            output_file = f"{self._output_dir}/{self._output_file}"
        fields = shape['fields']
        shaperecs = shape['shaperecs']
        with shapefile.Writer(output_file) as shp:
            shp.fields = fields
            for _, shaperec in shaperecs.items():
                shp.record(*shaperec['record'])
                shp.shape(shaperec['shape'])

        # pyshp doesn't allow specifying the projection of a shapefile so let's just
        # copy the projection file of the base shapefile. We need to remove .shp, if it's specified
        if self._base_shapefile[-4:] == '.shp':
            src_file = self._base_shapefile[:-4]
        else:
            src_file = self._base_shapefile

        if self._output_file[-4:] == '.shp':
            dest_file = self._output_file[:-4]
        else:
            dest_file = self._output_file

        copyfile(f"{src_file}.prj", f"{self._output_dir}/{dest_file}.prj")



if __name__ == "__main__":
    bla = CsvProcessor(base_shapefile='./shapefiles/base/COUNTIES')
    bla._load_shape()
    bla.process_csvs()
    #bla._save_shape(shape)