# search STRING_TO_FIND in the SOURCE_FILE
# get output through this command.
# result: times STRING_TO_FIND appears in SOURCE_FILE
text_search_command = """grep -o "<author>STRING_TO_FIND</author>" ./SOURCE_FILE | wc -l"""

def construct_text_search_command(author_name: str, source_file: str) -> str:
    temp = text_search_command
    temp = temp.replace("STRING_TO_FIND", author_name)
    temp = temp.replace("SOURCE_FILE", source_file)
    return temp