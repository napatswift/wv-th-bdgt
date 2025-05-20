import pandas as pd
import os
import openpyxl


def list_file_in_directory(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))

    return file_paths


def merge_csv_files(directory, output_file):
    """
    Add all csv files in the directory into a single xlsx file
    """
    file_paths = list_file_in_directory(directory)
    csv_file_paths = [
        file_path
        for file_path in file_paths
        if file_path.endswith('.csv')
    ]
    writer = pd.ExcelWriter(output_file, engine='openpyxl')
    for file_path in csv_file_paths:
        data_frame = pd.read_csv(file_path)
        file_name = os.path.basename(file_path)
        file_name = file_name.rsplit('.', 1)[0]
        data_frame.to_excel(writer, sheet_name=file_name[:30], index=False)

    writer.close()


if __name__ == '__main__':
    directory = 'output/2568'
    output_file = 'output.xlsx'
    merge_csv_files(directory, output_file)
    print('Done')
