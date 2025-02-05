from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, validators
from datetime import datetime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Mock database to store customer orders
customer_orders = {}


def generate_order_number():
    while True:
        order_num = f"{random.randint(1000, 9999)}"
        if order_num not in customer_orders:
            return order_num


class OrderLookupForm(FlaskForm):
    order_number = StringField('Order Number', [
        validators.DataRequired(),
        validators.Length(min=4, max=4, message='Order number must be 4 digits')
    ])
    contact_number = StringField('Contact Number', [
        validators.DataRequired(),
        validators.Regexp(r'^\d{8}$', message='Contact number must be 8 digits')
    ])


class DeliveryForm(FlaskForm):
    name = StringField('Name', [validators.DataRequired()])
    contact_number = StringField('Contact Number', [
        validators.DataRequired(),
        validators.Regexp(r'^\d{8}$', message='Contact number must be 8 digits')
    ])
    delivery_address = StringField('Delivery Address', [validators.DataRequired()])
    item_description = TextAreaField('Item Description', [validators.DataRequired()])
    pickup_date = StringField('Pickup Date', [
        validators.DataRequired(),
        validators.Regexp(r'^\d{4}-\d{2}-\d{2}$', message='Date must be in format YYYY-MM-DD')
    ])
    pickup_location = StringField('Pickup Location', [validators.Optional()])
    delivery_method = SelectField('Delivery Method', [validators.DataRequired()],
                                  choices=[
                                      ('standard', 'Standard Delivery'),
                                      ('express', 'Express Delivery'),
                                      ('same_day', 'Same Day Delivery')
                                  ])


@app.route('/')
def index():
    return redirect(url_for('schedule_delivery'))

# where the requirement of the date
@app.route('/schedule_delivery', methods=['GET', 'POST'])
def schedule_delivery():
    form = DeliveryForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            pickup_date = datetime.strptime(form.pickup_date.data, '%Y-%m-%d')
            if pickup_date.date() < datetime.now().date():
                flash('Pickup date must be in the future', 'error')
                return render_template('schedule_delivery.html', form=form)

            order_number = generate_order_number()

            order = {
                'order_number': order_number,
                'name': form.name.data,
                'contact_number': form.contact_number.data,
                'delivery_address': form.delivery_address.data,
                'item_description': form.item_description.data,
                'pickup_date': pickup_date.strftime('%Y-%m-%d'),
                'pickup_location': form.pickup_location.data,
                'delivery_method': dict(form.delivery_method.choices).get(form.delivery_method.data),
                'status': 'Pending',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            customer_orders[order_number] = order
            flash('Order created successfully', 'success')
            return render_template('delivery_confirmation.html', order=order)

        except ValueError:
            flash('Invalid date format', 'error')
            return render_template('schedule_delivery.html', form=form)

    return render_template('schedule_delivery.html', form=form)


@app.route('/edit_order/<string:order_number>', methods=['GET', 'POST'])
def edit_order(order_number):
    order = customer_orders.get(order_number)
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('customer_details'))

    form = DeliveryForm()

    if request.method == 'GET':
        # Pre-fill form with existing order data
        form.name.data = order['name']
        form.contact_number.data = order['contact_number']
        form.delivery_address.data = order['delivery_address']
        form.item_description.data = order['item_description']
        form.pickup_date.data = order['pickup_date']
        form.pickup_location.data = order['pickup_location']
        form.delivery_method.data = next(
            k for k, v in dict(form.delivery_method.choices).items() if v == order['delivery_method'])

    if request.method == 'POST' and form.validate_on_submit():
        try:
            pickup_date = datetime.strptime(form.pickup_date.data, '%Y-%m-%d')

            # Update order with new data
            order.update({
                'name': form.name.data,
                'contact_number': form.contact_number.data,
                'delivery_address': form.delivery_address.data,
                'item_description': form.item_description.data,
                'pickup_date': pickup_date.strftime('%Y-%m-%d'),
                'pickup_location': form.pickup_location.data,
                'delivery_method': dict(form.delivery_method.choices).get(form.delivery_method.data),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            customer_orders[order_number] = order
            flash('Order updated successfully', 'success')
            return redirect(url_for('customer_details'))

        except ValueError:
            flash('Invalid date format', 'error')

    return render_template('edit_order.html', form=form, order_number=order_number)

# after typing in the order number and number it will birng to another age
@app.route('/lookup_order', methods=['GET', 'POST'])
def lookup_order():
    form = OrderLookupForm()
    if request.method == 'POST' and form.validate_on_submit():
        order_number = form.order_number.data
        contact_number = form.contact_number.data

        order = customer_orders.get(order_number)

        if order and order['contact_number'] == contact_number:
            return render_template('order_found.html', order=order)
        else:
            flash('No matching order found. Please check your order number and contact number.', 'error')

    return render_template('lookup_order.html', form=form)


@app.route('/customer_details')
def customer_details():
    all_orders = list(customer_orders.values())
    sorted_orders = sorted(all_orders, key=lambda x: x['pickup_date'])
    return render_template('customer_details.html', orders=sorted_orders)


@app.route('/update_status/<string:order_number>/<string:status>')
def update_status(order_number, status):
    if order_number in customer_orders:
        customer_orders[order_number]['status'] = status
        flash(f'Order status updated to {status}', 'success')
    return redirect(url_for('customer_details'))


@app.route('/delete_order/<string:order_number>', methods=['POST'])
def delete_order(order_number):
    if order_number in customer_orders:
        del customer_orders[order_number]
        flash('Order has been successfully deleted', 'success')
    else:
        flash('Order not found', 'error')
    return redirect(url_for('customer_details'))


if __name__ == '__main__':
    app.run(debug=True)





