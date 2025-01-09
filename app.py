from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import stripe
import os
from dotenv import load_dotenv
from waitress import serve
import random
load_dotenv()



app = Flask(__name__)
app.config['SECRET_KEY'] = random.randint(1283912384983285352112414212412, 235723241421412427127421764217864722648712414371442984577285892734598271423154)  
app.config['SESSION_TYPE'] = 'filesystem'


stripe.api_key = os.getenv("STRIPE_PRIVATE")  
webhook_secret = os.getenv("STRIPE_WEBHOOK")  

PRODUCTS = {
    'ubuntu': {
        'name': 'Ubuntu Edition',
        'base_price': 2000
    },
    'pop_os': {
        'name': 'Pop!_OS Edition',
        'base_price': 3000
    },
    'arch': {
        'name': 'Arch Linux Edition',
        'base_price': 4000
    },
    'mint': {
        'name': 'Linux Mint Edition',
        'base_price': 2500
    }
}

STORAGE_PRICES = {
    '32': 700,    
    '64': 1200,   
    '128': 1700,  
    '256': 2700,  
    '512': 4200,  
    '1024': 9200  
}

@app.route("/create-checkout-session", methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        product_id = data.get('product')
        storage_size = data.get('storage')
        
        if product_id not in PRODUCTS:
            return jsonify({'error': 'Invalid product'}), 400
            
        product = PRODUCTS[product_id]
        
        # Generate order number
        order_number = f"DS-{random.randint(100000, 999999)}"
        
        customer_data = {
            'email': data.get('email'),
            'name': data.get('name'),
            'phone': data.get('phone'),
            'metadata': {
                'order_number': order_number,
                'product': product['name'],
                'storage_size': f"{storage_size}GB"
            },
            'address': {
                'line1': data.get('address'),
                'city': data.get('city'),
                'state': data.get('state'),
                'postal_code': data.get('zipCode'),
                'country': data.get('country'),
            },
            'shipping': {
                'name': data.get('name'),
                'address': {
                    'line1': data.get('address'),
                    'city': data.get('city'),
                    'state': data.get('state'),
                    'postal_code': data.get('zipCode'),
                    'country': data.get('country'),
                }
            }
        }
        
        customer = stripe.Customer.create(**customer_data)
        storage_price = STORAGE_PRICES.get(storage_size, 0)
        total_amount = product['base_price'] + storage_price

        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': total_amount,
                    'product_data': {
                        'name': f"{product['name']} with {storage_size}GB Storage. Includes the USB drive.",
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + f'success?session_id={{CHECKOUT_SESSION_ID}}&order={order_number}',
            cancel_url=request.host_url + 'pricing',
            metadata={
                'order_number': order_number,
                'product_id': product_id,
                'storage_size': storage_size,
                'usb_type': data.get('usbType'),
                'boot_mode': data.get('bootMode')
            }
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 403
    
@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid signature', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Update session in database to mark as completed
        session_id = session.id
        order_number = session.metadata.order_number
        
        print(f"Payment successful for Order #{order_number}: {session.metadata.product_id} with {session.metadata.storage_size}GB storage")

    return jsonify({'status': 'success'})

@app.route("/success")
def success():
    session_id = request.args.get('session_id')
    order_number = request.args.get('order')
    
    if not session_id or not order_number:
        return redirect(url_for('pricing'))
    
    try:
        # Verify this is a valid checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status != 'paid':
            return redirect(url_for('pricing'))
        
        # Get customer details
        customer = stripe.Customer.retrieve(checkout_session.customer)
        product_name = customer.metadata.product
        storage_size = customer.metadata.storage_size
        
        return render_template(
            "success.html",
            order_number=order_number,
            product_name=product_name,
            storage_size=storage_size
        )
    except Exception as e:
        print(e)
        return redirect(url_for('pricing'))
    
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

@app.route("/support")
def support():
    return render_template("legal.html")


if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)