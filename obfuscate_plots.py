import json
import os
import anthropic
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def obfuscate_plot(plot_text, client):
    """Use Claude to obfuscate a movie plot by removing identifying information."""

    prompt = f"""Please rewrite the following movie plot by removing all unique proper nouns and identifying features, but keep the general plotline the same.

Rules:
- Replace character names with generic pseudonyms (e.g., "John", "Sarah", "Detective Smith")
- Replace specific place names with generic descriptions (e.g., "Paris" → "a European city", "New York" → "a large city")
- Keep time periods, general settings, and occupations/roles as long as they're generic enough
- Preserve the story structure and key plot points
- Do NOT mention the movie title or any uniquely identifying details
- Keep it natural and readable
- Only put the obfuscated plot, do not put any other text into the output as we use it in JSON later

Original plot:
{plot_text}

Obfuscated plot:"""

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text.strip()

def process_single_file(json_file, output_dir, client):
    """Process a single movie file."""
    try:
        # Check if already processed
        output_file = Path(output_dir) / json_file.name
        if output_file.exists():
            return {'status': 'skipped', 'file': json_file.name}

        # Read original JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            movie_data = json.load(f)

        # Get plot
        plot = movie_data.get('plot')
        if not plot:
            return {'status': 'no_plot', 'file': json_file.name}

        # Obfuscate plot
        obfuscated = obfuscate_plot(plot, client)

        # Create new JSON with only obfuscated_plot
        output_data = {
            'obfuscated_plot': obfuscated
        }

        # Save to output directory
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return {'status': 'success', 'file': json_file.name}

    except Exception as e:
        return {'status': 'error', 'file': json_file.name, 'error': str(e)}

def process_movie_files(input_dir='movie_data', output_dir='obfuscated_movie_plot', max_workers=10):
    """Process all JSON files in the movie_data directory in parallel."""

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize Anthropic client
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Get all JSON files
    input_path = Path(input_dir)
    json_files = list(input_path.glob('*.json'))

    print(f"Found {len(json_files)} JSON files to process")
    print(f"Using {max_workers} parallel workers\n")

    processed = 0
    skipped = 0
    errors = []

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_single_file, json_file, output_dir, client): json_file
            for json_file in json_files
        }

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_file), 1):
            result = future.result()

            if result['status'] == 'success':
                print(f"[{i}/{len(json_files)}] ✓ Processed {result['file']}")
                processed += 1
            elif result['status'] == 'skipped':
                print(f"[{i}/{len(json_files)}] ⊘ Skipped {result['file']} (already exists)")
                skipped += 1
            elif result['status'] == 'no_plot':
                print(f"[{i}/{len(json_files)}] ⚠ Skipped {result['file']} (no plot)")
            elif result['status'] == 'error':
                error_msg = f"Error processing {result['file']}: {result['error']}"
                print(f"[{i}/{len(json_files)}] ✗ {error_msg}")
                errors.append(error_msg)

    print(f"\n✓ Done! Processed {processed} files, skipped {skipped} files")

    if errors:
        print(f"\n⚠ Encountered {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")

if __name__ == "__main__":
    process_movie_files()
