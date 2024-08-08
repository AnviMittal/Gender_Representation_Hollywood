import requests
import pandas as pd
import gender_guesser.detector as gender
import seaborn as sns
import matplotlib.pyplot as plt
import json
import time

# Replace 'your_api_key' with the actual API key you obtained from OMDb
api_key = 'eb75de5e'

# Function to fetch movie details by title
def fetch_movie_details(api_key, title):
    url = f'http://www.omdbapi.com/?apikey={api_key}&t={title}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for {title}. Status code: {response.status_code}")
        return None

# Function to fetch movies with pagination
def fetch_movies(api_key, search_term, max_pages = 1):
    all_results = []
    for page in range(1, max_pages + 1):
        url = f'http://www.omdbapi.com/?apikey={api_key}&s={search_term}&type=movie&page={page}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'Search' in data:
                all_results.extend(data['Search'])
                print(f"Fetched page {page} for search term '{search_term}'.")
            else:
                break  # No more results
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            break
        time.sleep(1)  # Sleep to avoid hitting rate limits
    return all_results

# Fetch data using multiple search terms and pagination
search_terms = [
    'action', 'comedy', 'drama', 'thriller', 'horror', 'romance', 'sci-fi', 'fantasy',
    'adventure', 'animation', 'biography', 'crime', 'documentary', 'family', 'history', 'musical',
    'mystery', 'sport', 'war', 'western'
]
all_results = []
for term in search_terms:
    results = fetch_movies(api_key, term, max_pages=1)
    all_results.extend(results)

# Convert the results to a DataFrame
df_movies = pd.DataFrame(all_results)

# Print the number of rows after initial fetch
print("Number of rows after initial fetch:", df_movies.shape[0])

# Fetch detailed information for each movie
movie_details = []
for title in df_movies['Title']:
    details = fetch_movie_details(api_key, title)
    if details:
        movie_details.append(details)
    print(f"Fetched details for {title}.")
    time.sleep(1)  # Sleep to avoid hitting rate limits

# Convert the detailed information to a DataFrame
df_movie_details = pd.DataFrame(movie_details)

# Extract lead characters
df_movie_details['LeadCharacter'] = df_movie_details['Actors'].apply(lambda x: x.split(',')[0] if pd.notnull(x) else None)
df_movie_details['Genre'] = df_movie_details['Genre'].apply(lambda x: x.split(',') if pd.notnull(x) else [])

# Explode genres into separate rows
df_movie_details = df_movie_details.explode('Genre')

# Drop rows with missing LeadCharacter values
df_movie_details = df_movie_details.dropna(subset=['LeadCharacter'])

# Print the number of rows after dropping missing LeadCharacter values
print("Number of rows after dropping missing LeadCharacter values:", df_movie_details.shape[0])

# Initialize the gender detector
detector = gender.Detector()

# Predict the gender of lead characters
def predict_gender(name):
    first_name = name.split()[0]  # Get the first name
    gender = detector.get_gender(first_name)
    if gender in ['female', 'mostly_female']:
        return 'female'
    elif gender in ['male', 'mostly_male']:
        return 'male'
    else:
        return 'unknown'

# Apply the gender prediction
df_movie_details['LeadGender'] = df_movie_details['LeadCharacter'].apply(predict_gender)

# Filter out unknown genders
df_movie_details = df_movie_details[df_movie_details['LeadGender'] != 'unknown']

# Print the number of rows after filtering unknown genders
print("Number of rows after filtering unknown genders:", df_movie_details.shape[0])

# Save the updated DataFrame
df_movie_details.to_csv('movies_with_gender.csv', index=False)

# Inspect the updated DataFrame
print(df_movie_details[['Title', 'LeadCharacter', 'LeadGender']].head())

# Calculate the proportion of female and male leads
lead_gender_counts = df_movie_details['LeadGender'].value_counts(normalize=True)

# Plot the proportions as a pie chart
proportions = lead_gender_counts.values
labels = lead_gender_counts.index
colors = ['#4c72b0', '#dd8452']

plt.figure(figsize=(8, 8))
wedges, texts, autotexts = plt.pie(proportions, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)

# Customize the labels and percentages
for i, text in enumerate(texts):
    x, y = text.get_position()
    if labels[i] == 'male':
        text.set_position((x - 0.15, y + 0.3))  # Adjust the position for 'Male'
    if labels[i] == 'female':
        text.set_position((x + 0.2, y - 0.3))  # Adjust the position for 'Female'
    text.set_fontsize(14)
    text.set_fontweight('bold')

for autotext in autotexts:
    autotext.set_fontsize(14)
    autotext.set_fontweight('bold')
    autotext.set_color('white')

plt.title('Proportion of Female vs Male Leads in Movies', fontsize=16)
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
plt.show()

