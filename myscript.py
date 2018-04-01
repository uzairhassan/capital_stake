#!/usr/bin/env python
# coding=utf-8
# coding=utf-8
"""
Module doc string to be inserted here.
"""
import bs4
import csv
import importlib
import json
import requests
import sys


def request_web_page(url):
    """Takes url as input and opens it"""
    try:
        return requests.get(url)
    # Handling no internet availability issue
    except IOError as error:
        print(error)
        return None


def get_pacra_ratings():
    """  Opens http://www.pacra.com.pk/reports.php and returns list of json objects  """
    calendar_map = {
        "Jan": "1",
        "Feb": "2",
        "Mar": "3",
        "Apr": "4",
        "May": "5",
        "Jun": "6",
        "Jul": "7",
        "Aug": "8",
        "Sep": "9",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12"
    }  # To map months to their number
    pacra_url = 'http://www.pacra.com.pk/reports.php'
    base_pacrs_url = 'http://www.pacra.com.pk/'
    pacra_data = []
    map_pacra_attributes = ["number", "name", "sector", "type", "date", "lt_rating", "st_rating", "action",
                            "outlook", "press_link", "report_link", "history_link"]
    attributes = []
    importlib.reload(sys)
    url_open = request_web_page(pacra_url)
    if url_open is None:
        return None
    page = url_open.text
    soup = bs4.BeautifulSoup(page, "html.parser")
    table_header = soup.find('tr', attrs={
        "style": "background: url(./images/templatePage/tab-onbig.png);font-size:10px;font-weight:bold"})
    for elements in table_header.contents:
        attributes.append(elements.text)
    div_containing_table = soup.find('div', attrs={
        "style": "overflow: auto;height:500px"})
    table = div_containing_table.contents[0]
    table_data = table.contents
    for index in range(1, len(table_data)):
        row = table_data[index].contents
        if row[3].text == 'Entity':
            entity_to_push = {}

            # Processing non file fields

            for row_index in range(0, 9):
                if attributes[row_index] != "No." and attributes[row_index] != "RatingType":
                    data = row[row_index].text
                    if map_pacra_attributes[row_index] == "date":
                        # Handling date file_format

                        split_date = data.split('-')
                        day = split_date[0]
                        month = split_date[1]
                        year = split_date[2]
                        year = str(int(year) + 2000)
                        data = year + "-" + calendar_map[month] + "-" + day
                    entity_to_push[map_pacra_attributes[row_index]] = data

            # Processing files fields

            for row_index in range(9, 12):
                content_link = row[row_index].contents
                if len(content_link) != 0:
                    if row[row_index].text != "-":
                        link = content_link[0].attrs['href']
                        link = link.split('/')
                        link.pop(0)
                        link.pop(0)
                        complete_link = ""
                        for links in link:
                            complete_link += links + "/"
                        complete_link = base_pacrs_url + complete_link
                        complete_link = complete_link[:-1]
                        entity_to_push[map_pacra_attributes[row_index]] = complete_link
                    else:
                        entity_to_push[map_pacra_attributes[row_index]] = ""
            pacra_data.append(entity_to_push)
    return pacra_data


def get_jcrvis_ratings():
    """  Opens http://jcrvis.com.pk/ratingSect.aspx and returns list of json objects  """
    jcrvis_url = "http://jcrvis.com.pk/ratingSect.aspx"
    base_url = "http://jcrvis.com.pk/"
    url_open = request_web_page(jcrvis_url)
    if url_open is None:
        return None
    page = url_open.text
    soup = bs4.BeautifulSoup(page, "html.parser")
    fields_list = soup.findAll('tr', class_="fields")
    attributes = fields_list[0].text.split('\n')

    # Removing empty fields returned by web page
    attributes.pop(0)
    attributes.pop(-1)

    div_table = soup.find('div', class_="ratings-data")
    desired_category = "Corporates"
    table = div_table.contents[1].contents
    index = -1
    desired_section_index = -1

    for element in table:
        index += 1
        if type(element) == bs4.element.Tag:
            if element.name == "thead":
                if 'id' in element.attrs:
                    if element.attrs['id'] == desired_category:
                        desired_section_index = index
                        break

    jcrvis_data = []
    map_jcrvis_attributes = ["name", "date", "type", "lt_rating", "st_rating", "outlook", "action"]
    map_jcrvis_file_attributes = ["press_link", "report_link", "history_link"]
    sector_field = "sector"
    sector = ""
    for index in range(413, len(table)):
        attribute_index = 0
        files_index = 0
        do_push = True
        element = table[index]
        if type(element) == bs4.element.Tag:
            entity_to_push = {}
            if element.name == "thead":
                if "class" in element.attrs:
                    if element.attrs['class'][0] == "sector-type":
                        break
            if element.name == "tbody":
                rows = element.contents
                for field in rows:
                    if type(field) == bs4.element.Tag:
                        if field.name == "tr":
                            if field.attrs['class'][0] == 'data':
                                for data in field.contents:
                                    if type(data) == bs4.element.Tag:
                                        data = data.text
                                        data = data.replace("\n", '')
                                        data = data.replace("\r", '')
                                        data = data.replace("\xa0", '')
                                        if "Long Term" == attributes[attribute_index] or attributes[
                                            attribute_index] == "Short Term" or attributes[attribute_index] == "Action":
                                            data = data.replace(" ", '')
                                        if attributes[attribute_index] == "Rating Type":
                                            if data != "Entity":
                                                do_push = False
                                                break
                                        if attributes[attribute_index] == "Date":
                                            #  Adjusting date file_format according to output required

                                            data = data.replace('/', '-')
                                            split_date = data.split('-')
                                            month = split_date[0]
                                            day = split_date[1]
                                            year = split_date[2]
                                            data = year + "-" + month + "-" + day
                                        if data != "Entity":
                                            entity_to_push[map_jcrvis_attributes[attribute_index]] = data
                                        attribute_index += 1

                            # Processing files field ie report, history, press

                            elif field.attrs['class'][0] == 'files':
                                list_files = field.contents[1].contents[1].contents
                                counter = 0
                                for related_file in list_files:
                                    if type(related_file) == bs4.element.Tag:
                                        for link in related_file.contents:
                                            if type(link) == bs4.element.Tag:
                                                entity_to_push[map_jcrvis_file_attributes[files_index]] = base_url + \
                                                                                                          link.attrs[
                                                                                                              'href']
                                                counter += 1
                                                files_index += 1
                                if counter < 3:
                                    entity_to_push[map_jcrvis_file_attributes[files_index]] = ""
                entity_to_push[sector_field] = sector
                if do_push:
                    jcrvis_data.append(entity_to_push)
            if element.name == "thead":
                if "class" in element.attrs:
                    if element.attrs['class'][0] == "sector-header":
                        sector = element.attrs['id']
    return jcrvis_data


def main(filename="output.json"):
    """
    Entry point. Collects all data and writes to file
    """
    print("Wait ... Fetching data")
    pacra_ratings = get_pacra_ratings()
    jcrvis_ratings = get_jcrvis_ratings()
    if pacra_ratings is None or jcrvis_ratings is None:
        print("\nTry again later")
        return
    data = pacra_ratings + jcrvis_ratings
    print("Now ... Saving data")
    file_format = filename.split('.')[1]
    if file_format == "json":
        with open(filename, 'w') as file_to_write:
            json.dump(data, file_to_write, indent=4)
    if file_format == "csv":
        outputFile = open(filename, 'w')  # open csv file
        output = csv.writer(outputFile)  # create a csv.write
        output.writerow(data[0].keys())  # header row
        for row in data:
            output.writerow(row.values())  # values row


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        main()
