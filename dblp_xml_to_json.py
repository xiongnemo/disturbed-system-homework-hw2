from marshmallow.common.utils.xml import xml_to_json
import sys

def xml_file_to_json_file(file_name: str):
    real_file_name = (file_name.split("."))[:-1]
    print("Reading " + file_name + ".")
    with open(file_name, 'r') as input_file:
        xml_data = input_file.read()
    print("Read complete. Begining XML to JSON process.")
    json_data = xml_to_json(xml_data)
    print("JSON generated. Began to write...")
    with open(real_file_name[0] + ".json", 'w') as output_file:
        output_file.write(json_data)
    print("Write complete!")

def main(argv):
    file_name = argv[0]
    xml_file_to_json_file(file_name)

if __name__ == '__main__':
    main(sys.argv[1:])