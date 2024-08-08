import os
import re
import gender_guesser.detector as gender
import matplotlib.pyplot as plt
import requests

detector = gender.Detector()

def count_lines(file_path):
    word = "dialog:" 
    count = 0
    with open(file_path, 'r', errors='ignore') as file:
        lines = file.readlines()
        for line in lines:
            if re.search(re.escape(word), line):
                count += 1
        return count 

api_keys = ['eb75de5e', 'a086b949', 'fe9e1032', '2a844301']

# Function to fetch movie details by title
def fetch_movie_details(title):
    i = 0 
    api_key = api_keys[i]
    url = f'http://www.omdbapi.com/?apikey={api_key}&t={title}'
    response = requests.get(url)
    if response.status_code == 401:
        if i < len(api_keys) - 1: i += 1
        api_key = api_keys[i]
        url = f'http://www.omdbapi.com/?apikey={api_key}&t={title}'
        response = requests.get(url)
    
    if response.status_code == 200:
        response = response.json()
        if "Genre" in response:
            return response["Genre"]
        elif 'Genre' in response: 
            return response['Genre']
        else: 
            return None 
    else:
        print(f"Failed to fetch data for {title}. Status code: {response.status_code}")
        return None

ratios = {}

def main():
    folder_path = '/Users/anvimittal/Downloads/archive (2)/movie_characters/data/movie_character_texts/movie_character_texts'
    total_male_lines = 0
    total_female_lines = 0
    nums = {}
    for dir_name in os.listdir(folder_path):
        dir_path = os.path.join(folder_path, dir_name)
        movie_name = re.sub(r'_\d+', '', dir_name)
        print(movie_name)
        genres = fetch_movie_details(movie_name)
        print(genres)
        male_lines = 0
        female_lines = 0
        if genres: 
            for file_name in os.listdir(dir_path):
                if file_name.endswith('.txt') and not file_name.startswith('.'):  # Ignore hidden and non-txt files
                    character_name = os.path.splitext(file_name)[0]
                    character_name = re.sub(r'_text', '', character_name)
                    char_gender = detector.get_gender(character_name.split()[0])  # Use the first name for gender detection
                    line_count = count_lines(os.path.join(dir_path, file_name))
                    print(f"Character: {character_name}, Gender: {char_gender}, Lines: {line_count}")  # Debug print
                    if char_gender in ['male', 'mostly_male']:
                        male_lines += line_count
                        total_male_lines += line_count
                    elif char_gender in ['female', 'mostly_female']:
                        female_lines += line_count
                        total_female_lines += line_count
                    if male_lines != 0 and female_lines != 0:
                        ratio = male_lines / female_lines
                    else: 
                        ratio = 0
            genre_list = [word.strip() for word in genres.split(',')]
            for genre in genre_list:
                if genre not in ratios.keys():
                    ratios[genre] = 0
                    nums[genre] = 0
                if ratio != 0:
                    ratios[genre] += ratio
                    nums[genre] += 1
        else: 
            pass
    
    print(f"Initial ratios: {ratios}")
    print(f"Num movies: {nums}")
    for key in ratios.keys():
        num = nums[key]
        ratios[key] = round(ratios[key] / num, 3)
    
    print(ratios)

    if 'Film-Noir' in ratios:
        del ratios['Film-Noir']
    if 'N/A' in ratios:
        del ratios['N/A']

    plot_results(list(ratios.keys()), list(ratios.values()))

def plot_results(genres, ratios):
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.bar(genres, ratios, color='purple')

    ax.set_xlabel('Genres')
    ax.set_ylabel('Average Ratio of Male to Female Lines')
    ax.set_title('Average Ratio of Male to Female Lines by Genre')

    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
