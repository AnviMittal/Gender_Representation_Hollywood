import requests
import pandas as pd
import gender_guesser.detector as gender
import matplotlib.pyplot as plt
import time

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
def fetch_movies(api_key, search_term, max_pages=5):
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
    results = fetch_movies(api_key, term, max_pages=5)
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

# Convert 'Year' to datetime for proper analysis
df_movie_details['Year'] = pd.to_datetime(df_movie_details['Year'], format='%Y', errors='coerce')

# Filter the dataframe for years between 1996 and 2024
df_filtered = df_movie_details[(df_movie_details['Year'].dt.year >= 1996) & (df_movie_details['Year'].dt.year <= 2024)]

# Group by year and gender to count the number of movies per year for each gender
gender_trends = df_filtered.groupby([df_filtered['Year'].dt.year, 'LeadGender']).size().unstack().fillna(0)

# Calculate the ratio of male to female lead roles each year
gender_trends['ratio'] = gender_trends['male'] / gender_trends['female']

# Plot the trends
plt.figure(figsize=(14, 8))
plt.scatter(gender_trends.index, gender_trends['ratio'], color='b')
plt.plot(gender_trends.index, gender_trends['ratio'], linestyle='-', color='b')
plt.title('Ratio of Male to Female Lead Roles Over Time')
plt.ylabel('Ratio of Male to Female Leads')
plt.xlabel('Year')
plt.xticks(range(1996, 2025, 5))
plt.grid(True)
plt.show()

df_movie_details.to_csv('movie_details.csv', index=False)
