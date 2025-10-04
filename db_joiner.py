import json
import os
from pathlib import Path

def main():
    # Define directories
    movie_data_dir = Path("movie_data")
    obfuscated_dir = Path("obfuscated_movie_plot")

    # Initialize result array
    movies = []

    # Get all JSON files from movie_data directory
    movie_data_files = list(movie_data_dir.glob("*.json"))

    for movie_file in movie_data_files:
        filename = movie_file.name
        obfuscated_file = obfuscated_dir / filename

        # Check if corresponding obfuscated file exists
        if obfuscated_file.exists():
            # Read both JSON files
            with open(movie_file, 'r', encoding='utf-8') as f:
                movie_data = json.load(f)

            with open(obfuscated_file, 'r', encoding='utf-8') as f:
                obfuscated_data = json.load(f)

            # Combine the data
            combined = {**movie_data, **obfuscated_data}
            movies.append(combined)
            print(f"Processed: {filename}")
        else:
            print(f"Warning: No obfuscated file found for {filename}")

    # Write output to db.json
    output_file = Path("db.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully created db.json with {len(movies)} movies")

if __name__ == "__main__":
    main()
