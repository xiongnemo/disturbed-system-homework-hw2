# split file to 
# get output through this command.
# result: times STRING_TO_FIND appears in SOURCE_FILE
split_file_command = """split -n l/NUMBER_TO_SPLIT FILE_NAME FILE_NAME"""

def construct_split_file_command(number_to_split: int, source_file: str) -> str:
    temp = split_file_command
    temp = temp.replace("NUMBER_TO_SPLIT", str(number_to_split))
    temp = temp.replace("FILE_NAME", source_file)
    return temp