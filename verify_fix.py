import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from index import scrape_topic

def test_scrape():
    print("Testing scrape_topic with fix...")
    topic = "banjir sumatra"
    try:
        # data, raw = scrape_topic(topic, limit=1)
        # However, scrape_topic prints a lot, so we'll see output in console.
        
        print(f"Calling scrape_topic('{topic}', limit=1)...")
        clean_data, raw_data = scrape_topic(topic, limit=1)
        
        print(f"\nResult Clean Data Count: {len(clean_data)}")
        print(f"Result Raw Data Count: {len(raw_data)}")
        
        if len(clean_data) > 0:
            print("SUCCESS: Data scraped successfully.")
            print(f"Sample Title: {clean_data[0]['judul']}")
        else:
            print("FAILURE: No data scraped.")

    except Exception as e:
        print(f"CRITICAL ERROR during verification: {e}")

if __name__ == "__main__":
    test_scrape()
