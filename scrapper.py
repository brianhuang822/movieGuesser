import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin

def get_best_picture_nominations():
    """Scrape the Oscar Best Picture page for all winners and nominees."""
    url = "https://en.wikipedia.org/wiki/Academy_Award_for_Best_Picture"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    movies = []

    # Stop words that indicate we've reached the statistics section
    stop_phrases = [
        "Production companies and distributors with multiple nominations and wins",
        "production company",
        "distributor"
    ]

    # Find all tables that contain nomination information
    tables = soup.find_all('table', class_='wikitable')

    for table in tables:
        # Check if this table or preceding heading contains stop phrases
        prev_elements = []
        current = table.find_previous_sibling()
        # Check up to 3 previous siblings for headings
        for _ in range(3):
            if current:
                prev_elements.append(current)
                current = current.find_previous_sibling()

        should_stop = False
        for element in prev_elements:
            element_text = element.get_text().lower()
            if any(phrase.lower() in element_text for phrase in stop_phrases):
                should_stop = True
                break

        if should_stop:
            break

        # Also check the table caption
        caption = table.find('caption')
        if caption:
            caption_text = caption.get_text().lower()
            if any(phrase.lower() in caption_text for phrase in stop_phrases):
                break

        # Check first header row for production company indicators
        first_row = table.find('tr')
        if first_row:
            header_text = first_row.get_text().lower()
            if 'production company' in header_text or 'nominations' in header_text and 'wins' in header_text:
                break

        rows = table.find_all('tr')
        current_year = None

        for row in rows:
            cells = row.find_all('td')

            # Check if first cell is a th (year cell with rowspan)
            year_th = row.find('th')
            if year_th:
                year_text = year_th.get_text(strip=True)
                # Extract year from text like "2010" or "2010 (83rd)"
                year_parts = ''.join(filter(str.isdigit, year_text.split('\n')[0]))
                if year_parts and len(year_parts) >= 4:
                    current_year = year_parts[:4]

            if len(cells) == 0:
                continue

            # Determine which cell contains the film
            # If we have 3 cells: could be Year(th) | Film | Producer OR Film | Producer | Something
            # If we have 2 cells: Film | Producer (year from previous rowspan)
            # If we have 1 cell: Film only

            film_cell = None
            if len(cells) >= 2:
                # Check if first cell looks like a year (all digits)
                first_cell_text = cells[0].get_text(strip=True)
                if first_cell_text and first_cell_text.replace('/', '').replace('(', '').replace(')', '').isdigit():
                    # First cell is year, film is second cell
                    film_cell = cells[1]
                else:
                    # First cell is film
                    film_cell = cells[0]
            elif len(cells) == 1:
                film_cell = cells[0]
            else:
                continue

            if not film_cell:
                continue

            # Get the first link in the film column (the film title)
            link = film_cell.find('a')
            if link:
                href = link.get('href')
                title = link.get_text(strip=True)

                # Skip non-article links
                if not href or not href.startswith('/wiki/'):
                    continue
                if ':' in href:  # Skip special pages
                    continue

                full_url = urljoin("https://en.wikipedia.org", href)

                if title and full_url:
                    movies.append({
                        'year': current_year,
                        'title': title,
                        'url': full_url
                    })

    return movies

def extract_plot_from_section(soup, section_name):
    """Helper function to extract plot text given a section name."""
    plot_section = None

    # Look for heading divs or h2/h3 tags with the section name
    for element in soup.find_all(['div', 'h2', 'h3']):
        if element.name == 'div' and 'mw-heading' in element.get('class', []):
            # Check if this heading contains the section name
            heading_text = element.get_text()
            if section_name.lower() in heading_text.lower():
                plot_section = element
                break
        elif element.name in ['h2', 'h3']:
            if section_name.lower() in element.get_text().lower():
                plot_section = element
                break

    if not plot_section:
        return None

    # Extract all paragraphs after the plot heading until the next main section
    plot_text = []
    current = plot_section.find_next_sibling()

    while current:
        # Stop at next main section heading (h2 level)
        if current.name == 'div' and 'mw-heading' in current.get('class', []):
            # Check if this is an h2 level heading (main section)
            h2_in_div = current.find('h2')
            if h2_in_div:
                break

        if current.name == 'h2':
            break

        # Extract paragraph text (skip sub-headings like h3)
        if current.name == 'p':
            text = current.get_text(separator=' ', strip=True)
            if text:
                plot_text.append(text)

        current = current.find_next_sibling()

    return ' '.join(plot_text) if plot_text else None


def extract_plot(movie_url):
    """Extract the plot section from a movie's Wikipedia page."""
    print(f"  Fetching plot from {movie_url}...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(movie_url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try "Plot" first
        plot_text = extract_plot_from_section(soup, "Plot")

        # If Plot not found or empty, try "Synopsis"
        if not plot_text:
            plot_text = extract_plot_from_section(soup, "Synopsis")

        if not plot_text:
            print(f"    No plot or synopsis section found")
            return None

        return plot_text

    except Exception as e:
        print(f"    Error fetching plot: {e}")
        return None

def get_movie_filepath(movie_title, movie_year, output_dir='movie_data'):
    """Generate filepath for a movie JSON file."""
    safe_title = "".join(c for c in movie_title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')
    filename = f"{movie_year}_{safe_title}.json"
    return os.path.join(output_dir, filename)

def movie_already_scraped(movie_title, movie_year, output_dir='movie_data'):
    """Check if a movie has already been scraped."""
    filepath = get_movie_filepath(movie_title, movie_year, output_dir)
    return os.path.exists(filepath)

def save_movie_to_json(movie_data, output_dir='movie_data'):
    """Save a movie's data to a JSON file."""
    os.makedirs(output_dir, exist_ok=True)

    filepath = get_movie_filepath(movie_data['name'], movie_data.get('year'), output_dir)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, indent=2, ensure_ascii=False)

    print(f"  Saved to {filepath}")

def backfill_wiki_links(movies, output_dir='movie_data'):
    """Add wiki links to existing JSON files that don't have them."""
    print("\nBackfilling wiki links to existing files...")
    updated = 0

    for movie in movies:
        filepath = get_movie_filepath(movie['title'], movie['year'], output_dir)

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                movie_data = json.load(f)

            # Only update if 'wiki' field doesn't exist
            if 'wiki' not in movie_data:
                movie_data['wiki'] = movie['url']

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(movie_data, f, indent=2, ensure_ascii=False)

                print(f"  Updated {filepath}")
                updated += 1

    print(f"Backfilled {updated} files with wiki links")

def main():
    print("Starting Oscar Best Picture scraper...\n")

    # Get all nominations
    movies = get_best_picture_nominations()
    print(f"\nFound {len(movies)} movie links\n")

    # Backfill wiki links for existing files
    backfill_wiki_links(movies)

    # Process each movie
    processed = 0
    skipped = 0
    no_plot_found = []

    for i, movie in enumerate(movies, 1):
        print(f"[{i}/{len(movies)}] Processing: {movie['title']}")

        # Check if already scraped
        if movie_already_scraped(movie['title'], movie['year']):
            print(f"  Already scraped, skipping...")
            skipped += 1
            continue

        plot = extract_plot(movie['url'])

        if plot:
            movie_data = {
                'year': movie['year'],
                'name': movie['title'],
                'plot': plot,
                'wiki': movie['url']
            }
            save_movie_to_json(movie_data)
            processed += 1
        else:
            # Track movies without plots
            no_plot_found.append({
                'title': movie['title'],
                'year': movie['year'],
                'url': movie['url']
            })

        # Be respectful to Wikipedia servers
        time.sleep(1)

    print(f"\n✓ Done! Processed {processed} new movies, skipped {skipped} existing movies.")

    # Report movies without plots
    if no_plot_found:
        print(f"\n⚠ Could not find plots for {len(no_plot_found)} movies:")
        for movie in no_plot_found:
            print(f"  - {movie['title']} ({movie['year']})")
            print(f"    {movie['url']}")
    else:
        print("\n✓ All movies had plots!")

if __name__ == "__main__":
    main()
