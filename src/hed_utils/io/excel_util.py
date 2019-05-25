from typing import List, Dict, Union
from pathlib import Path

from xlrd import open_workbook
from xlwt import XFStyle, Workbook

from hed_utils import log

FLOAT_FMT = XFStyle()
FLOAT_FMT.num_format_str = "##0.00"


@log.call(skip_args=["sheets"])
def write_sheets(sheets: Dict[str, List[Dict[str, Union[int, float, str]]]], file: str):
    """ Writes multiple sheets data to a file.

    The column names for each sheet are the keys of the first dict record.
    Automatically suffixes the file name with .xlsx if missing


    Arguments:
        sheets(dict)    A dict with format { "sheet name": [ sheet records as dicts ] }
        file(str)       The output destination file

    Returns:
        dst_path(str)  Absolute path to the output file

    """

    dst_path = str(Path(file if file.endswith(".xlsx") else f"{file}.xlsx").absolute())

    output_workbook = Workbook()

    for sheet_name, sheet_records in sheets.items():
        if isinstance(sheet_name, float):
            sheet_name = f"{sheet_name:.02f}"
        sheet = output_workbook.add_sheet(sheet_name)
        sheet.show_headers = True
        columns = list(sheet_records[0].keys())

        # write the headers
        for column_index, column_name in enumerate(columns):
            sheet.write(0, column_index, column_name)

        # write the records
        for row_index, record in enumerate(sheet_records):
            for column_index, column_name in enumerate(columns):
                value = record[column_name]
                if isinstance(value, float):
                    sheet.write(row_index + 1, column_index, value, FLOAT_FMT)
                else:
                    sheet.write(row_index + 1, column_index, value)

    output_workbook.save(dst_path)

    return dst_path


@log.call(log_result=False)
def read_sheets(file: str) -> Dict[str, List[Dict[str, Union[int, float, str]]]]:
    file = str(Path(file).absolute())
    result = dict()

    with open_workbook(file) as workbook:
        for worksheet in workbook.sheets():

            result[worksheet.name] = []

            headers = [worksheet.cell_value(0, column_index) for column_index in range(worksheet.ncols)]

            for row_index in range(1, worksheet.nrows):
                row_data = {headers[column_index]: worksheet.cell_value(row_index, column_index)
                            for column_index
                            in range(worksheet.ncols)}

                result[worksheet.name].append(row_data)

    return result
