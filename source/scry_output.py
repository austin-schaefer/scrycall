import time


# shortcuts for printing card attributes in the format string
ATTR_CODES = {
    '%n': '%{name}',
    '%m': '%{mana_cost}',
    '%c': '%{cmc}',
    '%y': '%{type_line}',
    '%p': '%{power}',
    '%t': '%{toughness}',
    '%l': '%{loyalty}',
    '%o': '%{oracle_text}',
    '%f': '%{flavor_text}',
}


# TODO: refactor/add...
# printing columns with '%|'
# printing iterative values with '?'
# handling oracle text (or other values) that contain a line break
# traversing urls with '/'
def print_data(data_list, format_string):
    print_lines = []
    for data in data_list:
        print_lines += get_print_lines_from_data(data, format_string)

    for line in print_lines:
        if line:
            print(line)


def get_print_lines_from_data(data, format_string):
    print_line = format_string
    # to handle multiple percent characters next to one another, replace '%%' with a unique placeholder first
    percent_placeholder = '[PERCENT_' + str(time.time()) + ']'
    while percent_placeholder in print_line:
        percent_placeholder = '[PERCENT_' + str(time.time()) + ']'
    print_line = print_line.replace('%%', percent_placeholder)

    print_lines = substitute_attributes_for_values(print_line, data)
    if not print_lines:
        return None

    # substitute the percent placeholder last
    for i in range(len(print_lines)):
        print_lines[i] = print_lines[i].replace(percent_placeholder, '%')
    return print_lines


def substitute_attributes_for_values(print_line, data):
    # substitute the attribute shortcuts '%x' with their long form '%{attribute}' strings
    for attr_code in ATTR_CODES:
        print_line = print_line.replace(attr_code, ATTR_CODES[attr_code])

    print_lines = []

    while True:
        # replace any '%{attribute}' strings with the correct value from the input data
        attribute_name = get_next_attribute_name(print_line)
        if attribute_name is None:
            # get_next_attribute_name() returns None when there are no more attributes to substitute
            break

        if '*' in attribute_name:
            # '*' in an attribute can generate multiple lines
            iterated_print_lines = iterate_attributes_in_print_line(print_line, attribute_name, data)
            for line in iterated_print_lines:
                print_lines += substitute_attributes_for_values(line, data)
            return print_lines

        else:
            attribute_value = get_attribute_value(attribute_name, data)
            # if any attribute value is None, do not print anything on this line
            if attribute_value is None:
                return []
            print_line = print_line.replace('%{' + attribute_name + '}', str(attribute_value))

    # even if only one line is printed, return it in a list so that it can be iterated in earlier functions
    print_lines.append(print_line)

    return print_lines


def get_next_attribute_name(line):
    # attributes are formatted like '%{attribute_name}'
    start_idx = line.find('%{')
    if start_idx == -1 or start_idx == len(line) - 2:
        return None
    end_idx = line.find('}', start_idx)
    if end_idx == -1:
        return None
    attr = line[start_idx + 2: end_idx]
    return attr


def get_attribute_value(attribute_name, data):
    # nested attributes can be chained together like '%{top.middle.bottom}'
    nested_attributes = attribute_name.split('.')
    attr_value = data
    for attr in nested_attributes:
        attr_value = get_value_from_json_object(attr, attr_value)
        if attr_value is None:
            return None
    return attr_value


def get_value_from_json_object(attr, data):
    if isinstance(data, dict):
        return data.get(attr)
    elif attr.isdigit():
        # if the given data is not a dictionary, treat the data as a list and the attribute as the index
        idx = int(attr)
        if 0 <= idx < len(data):
            return data[idx]
    return None


def iterate_attributes_in_print_line(print_line, attribute_name, data):
    # for each possible value that '*' produces for a given attribute,
    # create a new print_line, replacing the '*' with each possible individual value.

    if attribute_name.startswith('*'):
        star_idx = -1
        sub_attr_name = ''
        sub_attr_value = data
        attr_to_replace = '*'
    else:
        star_idx = attribute_name.find('.*')
        sub_attr_name = attribute_name[:star_idx]
        sub_attr_value = get_attribute_value(sub_attr_name, data)
        attr_to_replace = sub_attr_name + '.*'

    iterated_lines = []

    if isinstance(sub_attr_value, dict):
        values_to_iterate = sub_attr_value.keys()
    elif isinstance(sub_attr_value, list):
        values_to_iterate = range(len(sub_attr_value))
    else:
        values_to_iterate = range(len(str(sub_attr_value)))

    for sub_attr_value in values_to_iterate:
        new_sub_attr_name = attr_to_replace.replace('*', str(sub_attr_value))
        # if the print_line contains duplicate sub-attributes, all will be replaced here
        new_print_line = print_line.replace('%{' + attr_to_replace, '%{' + new_sub_attr_name)

        if '*' in attribute_name[star_idx + 2:]:
            # multiple stars in a single attribute are handled recursively
            new_attribute_name = attribute_name.replace(attr_to_replace, new_sub_attr_name, 1)
            iterated_lines += iterate_attributes_in_print_line(new_print_line, new_attribute_name, data)
        else:
            iterated_lines.append(new_print_line)

    return iterated_lines
