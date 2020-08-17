import json
import random
import sqlite3
import string

import requests
from flask import Flask, jsonify, make_response, request, render_template
import emaildata

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

def connect():
    global connection
    global cursor
    connection = sqlite3.connect("AoPSCoin.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()


def disconnect():
    connection.commit()
    connection.close()


# ------------------------------------------
# Functions for Users
@app.route("/login", methods=["POST"])
def login():
    req = request.get_json()
    username = req.get("username")
    password = req.get("password")
    url = "https://artofproblemsolving.com/ajax.php"
    payload = {'a': 'login',
               'username': username,
               'password': password}
    files = []
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    if response.json()["response"]["username"] is not None:
        print(response.json()["response"]["username"])
        token = get_token(response.json()["response"]["username"])
        return make_response(jsonify({"token": token}), 200)
    else:
        return make_response(400)


# Get Functions
def get_users():
    connect()
    cursor.execute("SELECT * FROM users")
    item = cursor.fetchall()
    users = []
    for user in item:
        users.append(format_user(user))
    disconnect()
    return users

@app.route("/get_user", methods=["POST"])
def get_user():  # Get single user
    req = request.get_json()
    user = get_username(req.get("token"))
    if user == "Error":
        return make_response(400)
    else:
        showCoins = False
        connect()
        cursor.execute("SELECT * FROM users WHERE name = ?", (user,))
        item = cursor.fetchone()
        disconnect()
        if item != "Invalid User":
            return make_response(jsonify((format_user(item, showCoins))), 200)
        else:
            new_user(user)
            connect()
            cursor.execute("SELECT * FROM users WHERE name = ?", (user,))
            item = cursor.fetchone()
            disconnect()
            return make_response(jsonify((format_user(item, showCoins))), 200)

@app.route("/get_username", methods=["POST"])
def get_name_from_token():
    req = request.get_json()
    token = req.get("token")
    if token == None:
        return make_response(jsonify({"response":"Error"}),400)
    else:
        connect()
        cursor.execute("SELECT name FROM users WHERE token = ?", (token,))
        count = 0
        for item in cursor:
            count += 1
        if count > 0:
            return make_response(jsonify({"username":get_username(token), "token":token}),200)
        else:
            return make_response(jsonify({"response":"Error"}),400)
        disconnect()

def get_username(token):
    if token == None:
        return "Error"
    else:
        connect()
        cursor.execute("SELECT name FROM users WHERE token = ?", (token,))
        item = cursor.fetchone()[0]
        if(item):
            return item
        else:
            return "Invalid User"
        disconnect()


def get_balance(user):  # Get balance of user
    connect()
    cursor.execute("SELECT coins FROM users WHERE name = ?", (user,))
    for item in cursor:
        return len(json.loads(item[0]))
    disconnect()

@app.route("/get_token", methods=["POST"])
def admin_get_token():
    req = request.get_json()
    token = req.get("token")
    user = req.get("user")
    valid_admins = ["casi","SamuraiA","AoPSCoin Central Bank","cw357","Pokemon!!!","IMO 2023"]
    emaildata.email(get_username(token)+" has requested the token of " + get_token(user),"New Token Request")
    if get_username(token) in valid_admins and user not in ["casi","AoPSCoin Central Bank","SamuraiA","cw357"]:
        return make_response(jsonify({"token":get_token(user)}),200)
    else:
        return make_response("Invalid permissions",403)

def get_token(user):
    if user_in_database(user):
        connect()
        cursor.execute("SELECT token FROM users WHERE name = ?", (user,))
        for item in cursor:
            token = item[0]
            if token == 'BLANK':
                connect()
                newToken = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                cursor.execute("UPDATE users SET token = ? WHERE name = ?", (newToken, user))
                disconnect()
                return newToken
            else:
                return token
        disconnect()
    else:
        new_user(user)
        connect()
        cursor.execute("SELECT token FROM users WHERE name = ?", (user,))
        for item in cursor:
            token = item[0]
            if token == 'BLANK':
                connect()
                newToken = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                cursor.execute("UPDATE users SET token = ? WHERE name = ?", (newToken, user))
                disconnect()
                return newToken
            else:
                return token
        disconnect()


def format_user(user, showCoins=False):
    user_id = user[0]
    name = user[1]
    balance = json.loads(user[2])
    if not showCoins:
        balance = len(balance)
    joinTime = user[3]
    isValid = user[4]
    return {"id": user_id, "name": name, "balance": balance, "joinTime": joinTime, "isValid": isValid}


def user_in_database(user):
    connect()
    cursor.execute("SELECT * FROM users WHERE name = ?", (user,))
    item = cursor.fetchone()
    disconnect()
    if item:
        return True
    else:
        return False


# Modification Functions
def new_user(name):
    if user_in_database(name):
        return make_response("User already exists", 400)
    else:
        connect()
        coins = json.dumps([])  # No coins (yet)
        cursor.execute('INSERT INTO users (name,coins) VALUES (?,?)', (name, coins))
        disconnect()
        return "User " + name + " created"


def delete_user(user):
    if user == "casi":
        raise Exception("Error in main.py, line 4: No module flask")
    elif user_in_database(user):
        validate(user)
        validate("casi")
        make_transfer(user, "casi", get_balance(user), "Account removal")
        connect()
        cursor.execute('DELETE FROM users WHERE name = ?', (user,))
        print("User " + user + " deleted")
        disconnect()
    else:
        print("No such user")


def is_valid(user):
    connect()
    cursor.execute("SELECT isValid FROM users WHERE name = ?", (user,))
    item = cursor.fetchone()
    disconnect()
    item = item[0]
    return item == 1


def invalidate(user):
    connect()
    cursor.execute("UPDATE users SET isValid = 0 WHERE name = ?", (user,))
    disconnect()


def validate(user):
    connect()
    cursor.execute("UPDATE users SET isValid = 1 WHERE name = ?", (user,))
    disconnect()


def take_coins(user, amount):
    connect()
    cursor.execute("SELECT coins FROM users WHERE name = ?", (user,))  # Get the coins by the username
    coins = json.loads(cursor.fetchall()[0][0])  # Pluck out the JSON with indexes and convert to list
    cursor.execute("UPDATE users SET coins = ? WHERE name = ?", (json.dumps(coins[amount:]), user))
    disconnect()
    return coins[:amount]


def give_coins(user, coins):
    connect()
    cursor.execute("SELECT coins FROM users WHERE name = ?", (user,))  # Get the coins by the username
    originalCoins = json.loads(cursor.fetchall()[0][0])  # Pluck out the JSON with indexes and convert to list
    for coin in coins:
        originalCoins.append(coin)  # Add the new coins
    cursor.execute("UPDATE users SET coins = ? WHERE name = ?",
                   (json.dumps(originalCoins), user))  # Set the user's coins as the updated coin set
    disconnect()


# ------------------------------------------
# Functions for Transactions

def new_transaction(fromUser, toUser, coins, notes):
    connect()
    cursor.execute('INSERT INTO transactions (fromUser,toUser,coins,notes) VALUES (?,?,?,?)',
                   (fromUser, toUser, json.dumps(coins), notes))
    email_transaction([fromUser, toUser, coins, notes])
    disconnect()


@app.route("/get_transactions", methods=["POST"])
def get_transactions():
    req = request.get_json()
    name = get_username(req.get("token"))
    connect()
    transactions = []
    if name:
        cursor.execute("SELECT * FROM transactions WHERE fromUser = ?", (name,))
        for sentTransaction in cursor:
            if format_transaction(sentTransaction, False, name)["notes"] != "Account removal":
                transactions.append(format_transaction(sentTransaction, False, name))
        cursor.execute("SELECT * FROM transactions WHERE toUser = ?", (name,))
        for receivedTransaction in cursor:
            transactions.append(format_transaction(receivedTransaction, True, name))
        disconnect()
        return make_response(jsonify(transactions), 200)
    else:
        return "You must submit a user"


def format_transaction(transaction, received, username):
    ID = transaction[0]
    fromUser = transaction[1]
    toUser = transaction[2]
    if fromUser == username:
        name = toUser
    elif toUser == username:
        name = fromUser
    amount = len(json.loads(transaction[3]))
    notes = transaction[4]
    transferTime = transaction[5]
    return {"id": ID, "name": name, "amount": amount, "received": received, "notes": notes,
            "transferTime": transferTime}


def email_transaction(transaction):
    emaildata.email(transaction)


# ------------------------------------------
# Transfer Function
@app.route("/transfer", methods=["POST"])
def transfer():
    req = request.get_json()
    fromUser = get_username(req.get("token"))
    toUsers = req.get("toUsers")
    amount = int(req.get("amount"))
    notes = req.get("notes")
    return transfer_coins(fromUser, toUsers, amount, notes)


def transfer_coins(fromUser, toUsers, amount, notes):
    if amount < 1:
        return "You must send at least 1 AoPSCoin!"
    else:
        if not is_valid(fromUser):  # Check if the sending user is valid
            return make_response("You have been invalidated.",200)
        else:  # If the sending user is valid
            to = []
            inValid = []
            for toUser in toUsers:  # All attempted sends
                if toUser == fromUser:
                    inValid.append(toUser)
                else:
                    if not user_in_database(toUser):  # Create a new user if need be, and then add them to the valid list
                        new_user(toUser)
                        to.append(toUser)
                    elif not is_valid(toUser):  # If the user is invalid, add to the invalid list
                        inValid.append(toUser)
                    else:  # If and only if the user is valid, add to the valid list
                        to.append(toUser)
            if get_balance(fromUser) > amount * len(to):  # Check that the sending user has enough money
                for toUser in to:  # Every valid user
                    coins = take_coins(fromUser, amount)  # Take the coins
                    give_coins(toUser, coins)  # Give to the recipient
                    new_transaction(fromUser, toUser, coins, notes)  # Add the transaction
                response = ""
                if len(to) > 0:
                    response += "Successfully transferred " + str(amount) + " AoPSCoins from " + fromUser + " to " + ', '.join(to) + ". "
                if len(inValid) > 0:
                    response += "The following users were invalid: " + ', '.join(inValid)
                return make_response(response,200)

            else:
                return make_response("Not enough money!",200)  # Not enough money

def make_transfer(fromUser,toUsers,amount,notes):
    if amount < 1:
        return "You must send at least 0 AoPSCoins!"
    else:
        if not is_valid(fromUser):  # Check if the sending user is valid
            return "You have been invalidated."
        else:  # If the sending user is valid
            to = []
            inValid = []
            for toUser in toUsers:  # All attempted sends
                if not user_in_database(toUser):  # Create a new user if need be, and then add them to the valid list
                    new_user(toUser)
                    to.append(toUser)
                elif not is_valid(toUser):  # If the user is invalid, add to the invalid list
                    inValid.append(toUser)
                else:  # If and only if the user is valid, add to the valid list
                    to.append(toUser)
            if get_balance(fromUser) > amount * len(to):  # Check that the sending user has enough money
                for toUser in to:  # Every valid user
                    coins = take_coins(fromUser, amount)  # Take the coins
                    give_coins(toUser, coins)  # Give to the recipient
                    new_transaction(fromUser, toUser, coins, notes)  # Add the transaction
                response = ""
                if len(to) > 0:
                    response += "Successfully transferred " + str(amount) + " AoPSCoins from " + fromUser + " to " + ', '.join(to) + ". "
                if len(inValid) > 0:
                    response += "The following users were invalid: " + ', '.join(inValid)
                return response,200

            else:
                return "Not enough money!" # Not enough money

if __name__ == "__main__":
    app.run(host='0.0.0.0')
