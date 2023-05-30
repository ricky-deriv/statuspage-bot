from datetime import datetime, timedelta

def create_table(data):
    # Determine the maximum width for each column
    col_widths = [max(len(str(item)) for item in col) for col in zip(*data)]
    table_lines = []
    header = '|'.join(item.center(width) for item, width in zip(data[0], col_widths))
    table_lines.append(header)
    separator = '+'.join('-' * width for width in col_widths)
    table_lines.append(separator)
    for row in data[1:]:
        row_line = '|'.join(str(item).ljust(width) for item, width in zip(row, col_widths))
        table_lines.append(row_line)
    table = '\n'.join(table_lines)
    
    return table

def convert_utc_to_gmt8(utc_datetime):
    utc_time = datetime.strptime(utc_datetime, "%Y-%m-%dT%H:%M:%SZ")
    gmt_plus_8_time = utc_time + timedelta(hours=8)
    gmt_plus_8_time_str = gmt_plus_8_time.strftime("%Y-%m-%d %H:%M:%S")
    return gmt_plus_8_time_str