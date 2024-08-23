import random
import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_caching import Cache

app = Flask(__name__)


# Local caching
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600 
cache = Cache(app)


# Get pokemon data based on name or ID
def get_data(pokemon_name_or_id): 
    # Determine if the input is a name or ID
    is_id = pokemon_name_or_id.isdigit()
    
    if is_id:
        # Use ID directly
        pokemon_id = pokemon_name_or_id
    else:
        # Use name to get the ID
        pokemon_name = pokemon_name_or_id.lower()
        base_url_name_to_id = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
        
        try: 
            # Fetch API data
            response = requests.get(base_url_name_to_id)
            response.raise_for_status()
            pokemon_data = response.json()
            pokemon_id = pokemon_data["id"]
                
        except requests.exceptions.HTTPError:
            # Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
            flash("An error occurred while fetching data. Please try again later.")
            return redirect("/error")
                
        except requests.exceptions.RequestException:
            # Handle other request-related errors (e.g., network issues)
            flash("A network error occurred. Please check your connection and try again.")
            return redirect("/error")
         
        # API URL for pokemon info
        base_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"
    
    # Generate cache key
    pokemon_data_key = f"pokemon_{pokemon_id}"
    
    # Check if data is cached
    # Return data if already cached
    cached_data = cache.get(pokemon_data_key)
    if cached_data:
        return cached_data
    
    try: 
        # Fetch API data
        response = requests.get(base_url)
        response.raise_for_status()
        pokemon_data = response.json()
            
    except requests.exceptions.HTTPError:
        # Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
        flash("An error occurred while fetching data. Please try again later.")
        return redirect("/error")
            
    except requests.exceptions.RequestException:
        # Handle other request-related errors (e.g., network issues)
        flash("A network error occurred. Please check your connection and try again.")
        return redirect("/error")

    # Cache the data
    cache.set(pokemon_data_key, pokemon_data)
    
    return pokemon_data


# Get pokemon data based on random ID
def get_random_data(random_number): 
    # API URL for pokemon info
    base_url = f"https://pokeapi.co/api/v2/pokemon-species/{random_number}"
    
    # Generate cache key
    pokemon_data_key = f"pokemon_{random_number}"
    
    # Check if data is cached
    # Return data if already cached
    cached_data = cache.get(pokemon_data_key)
    if cached_data:
        return cached_data
    
    try: 
        # Fetch API data
        response = requests.get(base_url)
        response.raise_for_status()
        random_pokemon_data = response.json()
            
    except requests.exceptions.HTTPError:
        # Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
        flash("An error occurred while fetching data. Please try again later.")
        return redirect("/error")
            
    except requests.exceptions.RequestException:
        # Handle other request-related errors (e.g., network issues)
        flash("A network error occurred. Please check your connection and try again.")
        return redirect("/error")

    # Cache the data
    cache.set(pokemon_data_key, random_pokemon_data)
    
    return random_pokemon_data


def generate_random_pokemon_id():
    # Generate cache Key
    pokemon_count_key = "pokemon_count"
    
    # Check if the count is cached
    cached_count = cache.get(pokemon_count_key)
    if cached_count:
        pokemon_count = cached_count
    else:
        # API URL for pokemon count
        base_url = "https://pokeapi.co/api/v2/pokemon-species/"
        
        try: 
            # Fetch API data
            response = requests.get(base_url)
            response.raise_for_status()
            pokemon_count = response.json().get("count")
            
        except requests.exceptions.HTTPError:
            # Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
            flash("An error occurred while fetching data. Please try again later.")
            return redirect("/error")
            
        except requests.exceptions.RequestException:
            # Handle other request-related errors (e.g., network issues)
            flash("A network error occurred. Please check your connection and try again.")
            return redirect("/error")
            
        # Cache the data
        cache.set(pokemon_count_key, pokemon_count, timeout=86400)
    
    # Generate random number based on available count
    random_id = random.randint(1, pokemon_count)
    
    return random_id
    
    
@app.route("/", methods=['GET','POST'])
def index():
    random_id = generate_random_pokemon_id()
    random_pokemon_data = get_random_data(random_id)
    random_name = random_pokemon_data["name"].replace("-", " ").title()
    random_ID = random_pokemon_data["id"]
    
    # POST request
    if request.method == 'POST':
        pokemon_name_or_id = request.form.get('pokemon')
        
        # Check if input is blank
        if not pokemon_name_or_id:
            flash("Invalid input!")
            return render_template("index.html", name=random_name, id=random_ID)
              
        try: 
            # Fetch API data
            pokemon_data = get_data(pokemon_name_or_id)
            
            name = pokemon_data["name"].replace("-", " ").title()
            id = pokemon_data["id"]
            
        except requests.exceptions.RequestException:
            flash("Pokemon not found!")
            return redirect("/")

        return redirect(url_for("search", name=name, id=id))
    
    # GET request
    return render_template("index.html", name=random_name, id=random_ID)


@app.route("/pokemon", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        pokemon_name_or_id = request.form.get('pokemon')
        
        if not pokemon_name_or_id:
            flash("Invalid input!")
            return redirect("/")
            
        try: 
            # Fetch API data
            pokemon_data = get_data(pokemon_name_or_id)
            
            name = pokemon_data["name"].replace("-", " ").title()
            id = pokemon_data["id"]
            
        except requests.exceptions.RequestException:
            flash("Pokemon not found!")
            return redirect("/")

        return render_template("search.html", name=name, id=id)
    
    # GET request
    name_param = request.args.get("name")
    id_param = request.args.get("id")
    return render_template("search.html", name=name_param.title(), id=id_param)


@app.route("/error")
def error():
    return render_template("error.html")