import atexit
from flask import Flask, render_template, jsonify, request
import requests
from pymongo import MongoClient
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()

uri = "mongodb+srv://200551381:Nomaan15@final-project.xv4a5.mongodb.net/?retryWrites=true&w=majority&appName=final-project"

def fetch_and_store_data():
    url = "https://api.coincap.io/v2/assets"
    response = requests.get(url)
    data = response.json()
    assets = data['data']

    # MongoDB connection
    client = MongoClient(uri)
    db = client["200551381"]
    collection = db["Crypto_Coins_Live"]

    if collection.count_documents({}) > 0:
        # If the collection is not empty, delete all records
        collection.delete_many({})

    for asset in assets:
        # Convert 'priceUsd' to a float
        asset['priceUsd'] = float(asset['priceUsd'])
        # Insert each asset into the MongoDB collection
        collection.insert_one(asset)

@app.route('/')
def display_data():
    fetch_and_store_data()
    client = MongoClient(uri)
    db = client["200551381"]
    collection = db["Crypto_Coins_Live"]
    # Retrieve data from MongoDB
    data = list(collection.find())
    
    # Render an HTML template and pass the data to it
    return render_template('index.html', data=data)

@app.route('/api/data/<string:crypto_name>', methods=['GET'])
def api_get_item_by_name(crypto_name):
    client = MongoClient(uri)
    db = client["200551381"]
    collection = db["Crypto_Coins_Live"]
    data = collection.find_one({'name': crypto_name}, {'_id': 0})
    if data:
        # Return data as JSON
        return jsonify(data)
    else:
        return jsonify({'error': 'Crypto not found'}), 404

@app.route('/api/data/range', methods=['GET'])
def api_get_range_items():
    start_price = float(request.args.get('start_price', 0))
    end_price = float(request.args.get('end_price', 10000000))

    client = MongoClient(uri)
    db = client["200551381"]
    collection = db["Crypto_Coins_Live"]

    # Retrieve data within the specified price range
    data = list(collection.find({'priceUsd': {'$gte': start_price, '$lte': end_price}}, {'_id': 0}))

    # Return data as JSON
    return jsonify(data)


@app.route('/api/data', methods=['GET'])
def api_data():
    client = MongoClient(uri)
    db = client["200551381"]
    collection = db["Crypto_Coins_Live"]

    data = list(collection.find({}, {'_id': 0}))

    # Return data as JSON
    return jsonify(data)

def periodic_data_acquisition():
    fetch_and_store_data()

if __name__ == '__main__':
    # Schedule data acquisition every 30 seconds
    scheduler.add_job(id='Scheduled task', func=periodic_data_acquisition, trigger='interval', seconds=60)
    scheduler.start()
 
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    app.run()
