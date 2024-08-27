import os
import random
import requests
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_caching import Cache


app = Flask(__name__)


SECRET_KEY = os.getenv('SECRET_KEY')
app.config[SECRET_KEY]

# Local caching
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 86400 
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
        base_url_name_to_id = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_name}"
        
        try: 
            # Fetch API data
            response = requests.get(base_url_name_to_id)
            response.raise_for_status()
            pokemon_data_1 = response.json()
            pokemon_id = pokemon_data_1["id"]
                
        except requests.exceptions.HTTPError:
            # Handle HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
            flash("Pokemon not found!")
            return redirect("/")
                
        except requests.exceptions.RequestException:
            # Handle other request-related errors (e.g., network issues)
            flash("A network error occurred. Please check your connection and try again.")
            return redirect("/error")
         
    # API URL for pokemon info
    base_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    
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
        flash("Pokemon not found!")
        return redirect("/")
            
    except requests.exceptions.RequestException:
        # Handle other request-related errors (e.g., network issues)
        flash("A network error occurred. Please check your connection and try again.")
        return redirect("/error")

    # Cache the data
    cache.set(pokemon_data_key, pokemon_data)
    
    return pokemon_data


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
        cache.set(pokemon_count_key, pokemon_count)
    
    # Generate random number based on available count
    random_id = random.randint(1, pokemon_count)
    
    return str(random_id)
    

@app.after_request
def add_cache_control(response):
    if request.endpoint in ['index', 'search']:
        response.headers['Cache-Control'] = 'public, max-age=86400'
    return response   
    
    
@app.route("/", methods=['GET','POST'])
def index():
    random_id = generate_random_pokemon_id()
    random_pokemon_data = get_data(random_id)
    random_name = random_pokemon_data["name"].replace("-", " ").title()
    random_ID = random_pokemon_data["id"]
    random_stats = random_pokemon_data["stats"]
    random_types = random_pokemon_data["types"]
    
    # POST request
    if request.method == 'POST':
        pokemon_name_or_id = request.form.get('pokemon').strip()
        
        # Check if input is blank
        if not pokemon_name_or_id or pokemon_name_or_id.startswith('0'):
            flash("Invalid input!")
            return render_template("index.html", name=random_name, id=random_ID, stats=random_stats, types=random_types)
              
        try: 
            # Fetch API data
            pokemon_data = get_data(pokemon_name_or_id)
            
            if not pokemon_data:
                raise TypeError("Pokemon not found")
    
            # Pokemon data
            name = pokemon_data["name"].replace("-", " ").title()
            pokemon_id = pokemon_data["id"]
            stats = pokemon_data["stats"]
            types = pokemon_data["types"]
            
            # Clear session for new search
            if session:
                session.clear()
            
            # Session method for storing data 
            # Sending data with url_for with no params needed, because of session storing (to avoid lengthy URL)
            session['name'] = name
            session['pokemon_id'] = pokemon_id
            session['stats'] = stats
            session['types'] = types
                
        except TypeError:
            flash("Pokemon not found!")
            return render_template("index.html", name=random_name, id=random_ID, stats=random_stats, types=random_types)
        
        except requests.exceptions.RequestException:
            flash("An error occurred while fetching data.")
            return render_template("index.html", name=random_name, id=random_ID, stats=random_stats, types=random_types)

        return redirect(url_for("search"))
    
    # GET request
    return render_template("index.html", name=random_name, id=random_ID, stats=random_stats, types=random_types)


@app.route("/pokemon", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        pokemon_name_or_id = request.form.get('pokemon').strip()
        
        if not pokemon_name_or_id or pokemon_name_or_id.startswith('0'):
            flash("Invalid input!")
            return redirect("/")
            
        try: 
            # Fetch API data
            pokemon_data = get_data(pokemon_name_or_id)           
            
            if not pokemon_data:
                raise TypeError("Pokemon not found")
            
            # Pokemon data
            name = pokemon_data["name"].replace("-", " ").title()
            pokemon_id = pokemon_data["id"]
            stats = pokemon_data["stats"]
            types = pokemon_data["types"]
        
        except TypeError:
            flash("Pokemon not found!")
            return redirect("/")
            
        except requests.exceptions.RequestException:
            flash("An error occurred while fetching data.")
            return redirect("/")

        return render_template("search.html", name=name, id=pokemon_id, stats=stats, types=types)
    
    # GET request
    name = session.get('name')
    pokemon_id = session.get('pokemon_id')
    stats = session.get('stats', {})
    types = session.get('types', {})
    
    return render_template("search.html", name=name.title(), id=pokemon_id, stats=stats, types=types)


@app.route("/error")
def error():
    return render_template("error.html")