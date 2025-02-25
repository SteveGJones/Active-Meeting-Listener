import json
import re


def parse_vtt(file_path):
    """
    Parses a VTT file into individual records.
    """
    records = []
    current_record = {
        "id": None,
        "event_id": None,
        "sequence": None,
        "start": None,
        "end": None,
        "speaker": None,
        "text": "",
    }
    timecode_regex = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})")
    id_regex = re.compile(r"^([\w-]+\/[\d-]+)")
    speaker_block_start = re.compile(r"<v (.+?)>")
    speaker_block_end = "</v>"

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                if current_record["start"] is not None:
                    records.append(current_record.copy())
                    current_record = {
                        "id": None,
                        "event_id": None,
                        "sequence": None,
                        "start": None,
                        "end": None,
                        "speaker": None,
                        "text": "",
                    }
            elif id_match := id_regex.match(line):
                current_record["id"] = id_match.group(1)
                event_id, sequence_info = id_match.group(1).split("/")[1].split("-")
                current_record["event_id"] = event_id
                current_record["sequence"] = sequence_info
            elif timecode_match := timecode_regex.match(line):
                current_record["start"], current_record["end"] = timecode_match.groups()
            elif speaker_start := speaker_block_start.match(line):
                current_record["speaker"] = speaker_start.group(1)
                # the text runs from after the speaker block to the end of the line OR until the speaker block end
                if speaker_block_end in line:
                    current_record["text"] += line.split(">", 1)[1].split("</v>", 1)[0].strip() + " "
                else:   
                    current_record["text"] += line.split(">", 1)[1].strip() + " "
            elif current_record.get("speaker"):
                # if the speaker is already set, keep appending text from all subsequent lines until we get the speaker block end
                # the block end is not included in the text

                current_record["text"] += line.split("</v>", 1)[0].strip() + " "

    if current_record["start"] is not None:
        records.append(current_record.copy())

    return records

def sort_records(records):
    """
    Sorts records by numeric event ID and sequence ID.
    """
    return sorted(records, key=lambda r: (int(r["event_id"]), int(r["sequence"])))

def collate_records(records):
    """
    Collates sorted records into single blocks by event ID.
    """
    collated = {}
    for record in records:
        event_id = record["event_id"]
        if event_id in collated:
            collated[event_id]["text"] += " " + record["text"]
            collated[event_id]["end"] = record["end"]
        else:
            collated[event_id] = {
                "id": record["id"],
                "event_id": event_id,
                "start": record["start"],
                "end": record["end"],
                "speaker": record["speaker"],
                "text": record["text"],
            }

    return list(collated.values())

# Create a function that takes the sorted and collated list of records and determines if more collation is possible
# this uses the sorted list based on event_id, and if the speaker on subsequent records is the same, it collates them
# into a single record, it adds a new field "collated events" to record the collated event_ids and uses the first event_id
# as the main event_id
def collate_records_v2(records):
    """
    Collates sorted records into single blocks by event ID.
    """
    collated = []
    current_collation = None
    for record in records:
        if current_collation is None:
            current_collation = {
                "id": record["id"],
                "event_id": record["event_id"],
                "start": record["start"],
                "end": record["end"],
                "speaker": record["speaker"],
                "text": record["text"],
                "collated_events": [record["event_id"]],
            }
        elif current_collation["speaker"] == record["speaker"]:
            current_collation["text"] += " " + record["text"]
            current_collation["end"] = record["end"]
            current_collation["collated_events"].append(record["event_id"])
        else:
            collated.append(current_collation)
            current_collation = {
                "id": record["id"],
                "event_id": record["event_id"],
                "start": record["start"],
                "end": record["end"],
                "speaker": record["speaker"],
                "text": record["text"],
                "collated_events": [record["event_id"]],
            }

    if current_collation:
        collated.append(current_collation)

    return collated

def process_vtt_to_dictionary(vtt_file_path):
    """
    Parses, sorts, collates VTT records, and converts to a dictionary .
    The final list is sorted by event_id.
    """
    records = parse_vtt(vtt_file_path)  # Parse records
    sorted_records = sort_records(records)  # Sort records by event_id and sequence_id
    collated_records = collate_records(sorted_records)  # Collate by event_id
    # Sort the final collated records by event_id
    final_sorted_records = sorted(collated_records, key=lambda r: int(r["event_id"]))
    return_value = collate_records_v2(final_sorted_records)
    return return_value


def process_vtt_to_json(vtt_file_path, output_json_path):
    """
    Parses, sorts, collates VTT records, and converts to a JSON file.
    The final list is sorted by event_id.
    """
    results = process_vtt_to_dictionary(vtt_file_path)
    # Save to JSON
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

# create a main method which is given an input vtt file and an output json file
# it will call the process_vtt_to_json method to convert the vtt file to json
# validate that two arguments are provided, and that the input file exists
# if the output file exists, ask the user if they want to overwrite it
# if the user says no, exit the program
# if the user says yes, overwrite the file
# if the output file does not exist, create the file and write the json to it
# if the input file does not exist, print an error message and exit the program
def main():
    import sys
    import os

    print(f"VTT Parser {sys.argv}")

    if len(sys.argv) != 3:
        print("Usage: python vttparser.py <input_vtt_file> <output_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    if os.path.exists(output_file):
        choice = input(f"Output file '{output_file}' already exists. Overwrite? (y/n): ")
        if choice.lower() != "y":
            sys.exit(0)

    process_vtt_to_json(input_file, output_file)

if __name__ == "__main__":
    main()



