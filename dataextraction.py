# from bs4 import BeautifulSoup
# import requests

# resp = requests.get('https://example.com')
# soup = BeautifulSoup(resp.text, 'html.parser')

# # Get all <p> tags
# paragraphs = soup.find_all('p')

# # Print strings inside each <p>
# for p in paragraphs:
#     print(p.string)
import os

# Ensure file exists
if not os.path.exists('readandwrite.txt'):
    with open('readandwrite.txt', 'w') as f:
        f.write('Sample line one.\nAnother line here.')

# Create/append words to 'words.txt'
with open('readandwrite.txt', 'r') as file:
    for line in file:
        words = line.strip().split(' ')
        with open('words.txt', 'a') as f:
            for word in words:
                f.write(word.strip() + '\n')
        print(words)  # Optional: print words from each line

# Read back all contents from 'words.txt'
print("\n--- Contents of words.txt ---")
with open('words.txt', 'r') as file:
    file_content = file.read()
    print(file_content)

