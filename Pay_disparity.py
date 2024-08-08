import requests
import pandas as pd
import gender_guesser.detector as gender
import seaborn as sns
import matplotlib.pyplot as plt
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
def fetch_movies(api_key, search_term, max_pages=10):
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
search_terms = ['action', 'comedy', 'drama', 'thriller', 'horror', 'romance', 'sci-fi', 'fantasy',
                'adventure', 'animation', 'biography', 'crime', 'documentary', 'family', 'history',
                'musical', 'mystery', 'sport', 'war', 'western']
all_results = []
for term in search_terms:
    results = fetch_movies(api_key, term, max_pages=10)  # Reduced max_pages for faster execution
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

# Save the updated DataFrame for further use
df_movie_details.to_csv('movies_with_gender.csv', index=False)

# Inspect the updated DataFrame
print(df_movie_details[['Title', 'LeadCharacter', 'LeadGender']].head())

# Load the Forbes dataset (update the path to your actual file location)
df_forbes = pd.read_csv('/Users/anvimittal/Downloads/forbes_celebrity_100.csv')

# Inspect the Forbes dataset
print(df_forbes.head())

# Merge on actor names (ensure columns have common keys)
df_combined = pd.merge(df_movie_details, df_forbes, left_on='LeadCharacter', right_on='Name', how='inner')

# Inspect the merged DataFrame
print(df_combined.head())
print(df_combined.info())

# Calculate average earnings by gender
average_earnings_by_gender = df_combined.groupby('LeadGender')['Pay (USD millions)'].mean()

# Print the average earnings
print(average_earnings_by_gender)

# Visualization

# Bar plot for average earnings by gender
sns.barplot(x=average_earnings_by_gender.index, y=average_earnings_by_gender.values)
plt.title('Average Earnings by Gender')
plt.ylabel('Average Earnings in USD Millions')
plt.show()
