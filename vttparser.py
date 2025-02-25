import json
import re

# The parse_vtt function is responsible for parsing a Microsoft Teams VTT file into individual records.
# Each record contains metadata (like id, event_id, sequence, start/end time) and text content, including speaker information.
def parse_vtt(file_path):
    """
    Parses a VTT file into individual records.
    
    The expected record structure includes:
    - id: Unique identifier extracted from the VTT block label.
    - event_id: Derived from the id to represent the event.
    - sequence: Sequence id parsed from the id.
    - start: Start time extracted from the timecode line.
    - end: End time extracted from the timecode line.
    - speaker: Speaker identifier if available.
    - text: Captured transcription text.
    """
    records = []
    # Initialize an empty record structure with default values.
    current_record = {
        "id": None,
        "event_id": None,
        "sequence": None,
        "start": None,
        "end": None,
        "speaker": None,
        "text": "",
    }
    # Compile regex patterns for matching timecodes, IDs, and speaker tags.
    timecode_regex = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})")
    id_regex = re.compile(r"^([\w-]+\/[\d-]+)")
    speaker_block_start = re.compile(r"<v (.+?)>")
    speaker_block_end = "</v>"

    # Open the VTT file, read it line by line.
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # Remove leading/trailing whitespace.
            line = line.strip()
            # An empty line indicates the end of a record.
            if not line:
                if current_record["start"] is not None:
                    # Append a copy of the current record to the records list.
                    records.append(current_record.copy())
                    # Reset the current record for the next block.
                    current_record = {
                        "id": None,
                        "event_id": None,
                        "sequence": None,
                        "start": None,
                        "end": None,
                        "speaker": None,
                        "text": "",
                    }
            # Check if the line contains an identifier for the record.
            elif id_match := id_regex.match(line):
                current_record["id"] = id_match.group(1)
                # Extract event_id and sequence information from the id string.
                event_id, sequence_info = id_match.group(1).split("/")[1].split("-")
                current_record["event_id"] = event_id
                current_record["sequence"] = sequence_info
            # Check for the presence of the timecode line.
            elif timecode_match := timecode_regex.match(line):
                # Capture the start and end times.
                current_record["start"], current_record["end"] = timecode_match.groups()
            # Check for speaker info using the <v ...> tag.
            elif speaker_start := speaker_block_start.match(line):
                # Set the speaker identifier.
                current_record["speaker"] = speaker_start.group(1)
                # Determine if the text is confined to the same line (enclosed by </v>) or continues across lines.
                if speaker_block_end in line:
                    current_record["text"] += line.split(">", 1)[1].split("</v>", 1)[0].strip() + " "
                else:
                    # Append text from the current line after the speaker block.
                    current_record["text"] += line.split(">", 1)[1].strip() + " "
            elif current_record.get("speaker"):
                # For lines after the speaker tag that still belong to the same speaker block.
                # The block end marker is removed if present.
                current_record["text"] += line.split("</v>", 1)[0].strip() + " "

    # Append the last record if it hasn't been added yet.
    if current_record["start"] is not None:
        records.append(current_record.copy())

    return records

# The sort_records function sorts parsed records based on the numeric values of event_id and sequence.
def sort_records(records):
    """
    Sorts records by numeric event ID and sequence ID.
    
    This ensures that records are processed in the right time order.
    """
    return sorted(records, key=lambda r: (int(r["event_id"]), int(r["sequence"])))

# The collate_records function aggregates records based on their event_id.
# When multiple records share the same event_id, their text content is concatenated.
def collate_records(records):
    """
    Collates sorted records into single blocks by event ID.
    
    For records with the same event_id, combine the text contents and update the end time.
    """
    collated = {}
    for record in records:
        event_id = record["event_id"]
        if event_id in collated:
            # Append text from the current record.
            collated[event_id]["text"] += " " + record["text"]
            # The end timestamp is updated to the most recent record's end time.
            collated[event_id]["end"] = record["end"]
        else:
            # Create a new entry if the event_id is not already in the collated dictionary.
            collated[event_id] = {
                "id": record["id"],
                "event_id": event_id,
                "start": record["start"],
                "end": record["end"],
                "speaker": record["speaker"],
                "text": record["text"],
            }

    # Return a list of collated record dictionaries.
    return list(collated.values())

# The collate_records_v2 function further collates records from a sorted list.
# It checks if the speaker in subsequent records is the same, allowing multiple events by the same speaker to be combined.
# A new field "collated_events" is added to track the originating event_ids.
def collate_records_v2(records):
    """
    Further collates sorted records by checking speaker consistency.
    
    If subsequent records have the same speaker, merge them into one record and record all collated event_ids.
    The initial event_id is retained as the main event_id.
    """
    collated = []
    current_collation = None
    for record in records:
        if current_collation is None:
            # Initialize a new collation block with the details of the first record.
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
            # If the speaker remains the same, merge the text and update the end time.
            current_collation["text"] += " " + record["text"]
            current_collation["end"] = record["end"]
            current_collation["collated_events"].append(record["event_id"])
        else:
            # When the speaker changes, finalize the current collation and start a new one.
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
        # Append any remaining collation.
        collated.append(current_collation)

    return collated

# The process_vtt_to_dictionary function orchestrates the whole process:
# It parses the VTT file, sorts the records, collates them twice (first by event and then by speaker),
# and returns a final list of dictionaries ready for JSON conversion.
def process_vtt_to_dictionary(vtt_file_path):
    """
    Processes a VTT file into a dictionary structure.
    
    Steps involved:
    1. Parse the VTT file to get individual records.
    2. Sort the records by event_id and sequence.
    3. Collate records by event_id.
    4. Further collate records by speaker.
    5. Return the final structured list.
    """
    records = parse_vtt(vtt_file_path)  # Parse records
    sorted_records = sort_records(records)  # Sort records by event_id and sequence_id
    collated_records = collate_records(sorted_records)  # Collate by event_id
    # Sort the final collated records by event_id (in numeric order)
    final_sorted_records = sorted(collated_records, key=lambda r: int(r["event_id"]))
    return_value = collate_records_v2(final_sorted_records)
    return return_value

# The process_vtt_to_json function drives the conversion from a VTT file to a structured JSON file.
# It uses process_vtt_to_dictionary to process the file and then writes out the results to the given JSON path.
def process_vtt_to_json(vtt_file_path, output_json_path):
    """
    Processes a VTT file and saves the structured output as a JSON file.

    This involves parsing, sorting, collating, and then dumping the data in JSON format.
    """
    results = process_vtt_to_dictionary(vtt_file_path)
    # Write the results to a JSON file with pretty printing enabled.
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)

# The main function serves as the entry point when the program is executed from the command line.
# It validates the input and output file paths, checks for file existence, and requests user confirmation for overwriting.
def main():
    import sys
    import os

    # Display invocation information for debugging purposes.
    print(f"VTT Parser {sys.argv}")

    # Check for correct number of command-line arguments.
    if len(sys.argv) != 3:
        print("Usage: python vttparser.py <input_vtt_file> <output_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Validate that the input VTT file exists.
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    # If the output file already exists, prompt the user for permission to overwrite it.
    if os.path.exists(output_file):
        choice = input(f"Output file '{output_file}' already exists. Overwrite? (y/n): ")
        if choice.lower() != "y":
            sys.exit(0)

    # Process the VTT file and write the results to the output JSON file.
    process_vtt_to_json(input_file, output_file)

# Execute the main function if this script is run as the main module.
if __name__ == "__main__":
    main()
