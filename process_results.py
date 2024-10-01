import os
import json

def process_results_folder():
    results_folder = 'results'
    combined_data = []

    # Check if the results folder exists
    if not os.path.exists(results_folder):
        print(f"Error: The '{results_folder}' folder does not exist.")
        return

    # Iterate through all files in the results folder
    for filename in os.listdir(results_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(results_folder, filename)
            
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    combined_data.append(data)
                    
                    # Print content except for the "image" key
                    print(f"\nContent of {filename}:")
                    for key, value in data.items():
                        if key != "image":
                            print(f"{key}: {value}")
            except json.JSONDecodeError:
                print(f"Error: Unable to parse JSON in file '{filename}'. Skipping.")
            except IOError:
                print(f"Error: Unable to read file '{filename}'. Skipping.")

    for data in combined_data[-3:]:
        data['status'] = 'tentative'

    # Save the combined data to results.json
    output_file = 'results.json'
    try:
        with open(output_file, 'w') as file:
            json.dump(combined_data, file, indent=2)
        print(f"\nCombined {len(combined_data)} JSON files into '{output_file}'.")
    except IOError:
        print(f"Error: Unable to write to '{output_file}'.")

    return combined_data

if __name__ == "__main__":
    process_results_folder()