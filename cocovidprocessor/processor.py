import pandas as pd
import os
import re
import shapefile
from collections import defaultdict
from shutil import copyfile
from glob import glob

import pprint

class CsvProcessor:
    def __init__(self, base_shapefile, data_dir='downloads', output_dir='shapefiles', output_file=None):
        self._data_dir = data_dir
        self._base_shapefile = base_shapefile
        self._output_dir = output_dir
        # if an output_file name isn't specified, just assume the same name as the input
        self._output_file = output_file if None else re.split("\/|\\\\", base_shapefile)[-1]


    def process_single_csv(self, file):
        try:
            file_contents = pd.read_csv(file)
        except pd.errors.EmptyDataError as e:
            print(f"File {file} doesn't contain any contents: {e}")

        stat_list = defaultdict(dict)
        bla = {}
        for __, row in file_contents.iterrows():
            # Skip the following types of rows:
            # 1. Rows that contain state level data
            # 2. Rows that contain notes
            if (not re.search(r".*by County$", row['description']) or
                row['attribute'] == "Note"):
                continue

            # filter out all these extraneous words
            statistic = re.sub('in Colorado|by County|Colorado|Total|Per [10,]+ People', '', row['description']).strip()

            # Since there is a 10 char limit in attribute tables, we need to create a mapping
            # to shorten all these names
            if statistic == "Case Counts":
                statistic = "CASECOUNT"
            # This specific statstic is broken down into sub categories
            elif statistic == 'COVID-19 Tests Performed':
                if row['metric'] == "Total Tests Performed":
                    statistic = "TOTALTESTS"
                elif "Serology" in row['metric']:
                    statistic = "SEROLOGY"
                elif "PCR" in row['metric']:
                    statistic = "PCR"
                else:
                    print(f"New COVID-19 Test detected: {row['metric']}")
                    continue
            elif statistic == "Case Rates":
                statistic = "CASEPER100"
            elif statistic == "Number of Deaths":
                statistic = "DEATHS"
            elif statistic == "Testing Rate":
                statistic = "TESTRATE"
            else:
                print(f"New statistic detected: {statistic}")
                continue

            # sanitize/normalize the county names
            county = row['attribute'].replace(" County", "")
            stat_list[county][statistic] = row['value']

        pprint.pprint(stat_list)


    def process_csvs(self):
        file_list = glob(f"{self._data_dir}/*05-23.csv")
        for file in file_list:
            self.process_single_csv(file)


    # Load the contents of the shapefile into a dict as follows:
    # fields - contains the pyshp formatted list of fields
    # shape - an dict of dicts that contains every row in the existing shapefile. We
    #         key off the name of the column to make updating existing counties easier
    def _load_shape(self):
        shapes = {}
        with shapefile.Reader(self._base_shapefile) as shp:
            fields = shp.fields[1:]
            for shaperec in shp.iterShapeRecords():
                shapes[shaperec.record[0]] = {
                    "record": shaperec.record,
                    "shape": shaperec.shape
                }

            return {
                "fields" : fields,
                "shaperecs": shapes,
            }


    # takes a dict as defined in _load_shape() and saves that intp a shapefile. We
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
        # copy the projection file of the original truncate .shp, if it's specified
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
    bla.process_csvs()
    #shape = bla._load_shape()
    #bla._save_shape(shape)