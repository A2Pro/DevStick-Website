from flask import Flask, render_template, redirect, url_for, session, request
app = Flask(__name__)



PRODUCTS = {
    'ubuntu': {
        'name': 'Ubuntu Edition',
        'price': 2000, 
        'price_id': 'your_stripe_price_id_for_ubuntu'
    },
    'pop_os': {
        'name': 'Pop!_OS Edition',
        'price': 3000,
        'price_id': 'your_stripe_price_id_for_pop_os'
    },
    'arch': {
        'name': 'Arch Linux Edition',
        'price': 4000, 
        'price_id': 'your_stripe_price_id_for_arch'
    },
    'mint': {
        'name': 'Linux Mint Edition',
        'price': 2500,
        'price_id': 'your_stripe_price_id_for_mint'
    }
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/docs")
def docs():
    return render_template("docs.html")


if __name__ == '__main__':
    app.run(port=2349, host='0.0.0.0')