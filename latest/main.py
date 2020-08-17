import html
import io
import json
import random
import sqlite3
import string
import tempfile
from datetime import datetime

import emaildata as emaildata
import forum_scraper as scraper
import recorder
import requests
from flask import Flask, jsonify, make_response, request, send_file
from matplotlib import pyplot as plt

app = Flask(__name__)


# ------------------------------------------
# All valid paths
@app.route("/")
def home():
    return make_response("Welcome to the AoPSCoin server!", 200)


@app.route("/login", methods=["POST"])
def login():
    """login() (Called from Flask) -> Attempts to log into AoPS with provided credentials.
     If successful, returns user token."""

    # Get items from request
    req = request.get_json()
    username = req.get("username")
    password = req.get("password")

    # Send request to AoPS
    url = "https://artofproblemsolving.com/ajax.php"
    payload = {'a': 'login',
               'username': username,
               'password': password}
    files = []
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    if response.json()["response"]["username"] is not None:  # Check to see if the request went through
        token = get_token(response.json()["response"]["username"])  # If so, return the token
        return make_response(jsonify({"token": token}), 200)
    else:
        return make_response(400)


@app.route("/get_user", methods=["POST"])
def request_get_user():  # Get single user
    """get_user() (called from flask) -> Returns response of JSON with formatted user"""
    req = request.get_json()
    user = get_username(req.get("token"))  # The token is the reference
    if user == "Error":  # This is if there is no such user
        return make_response(400)
    else:  # If there is a user
        showCoins = False  # By default, we don't show the coins, just the balance
        connect()
        cursor.execute("SELECT * FROM users WHERE name = ?", (user,))  # Select user from database
        item = cursor.fetchone()
        disconnect()
        if item != "Invalid User":  # If user exists, return formatted user
            return make_response(jsonify((format_user(item, showCoins))), 200)
        else:  # Otherwise, create the user and return that
            new_user(user)
            connect()
            cursor.execute("SELECT * FROM users WHERE name = ?", (user,))
            item = cursor.fetchone()
            disconnect()
            return make_response(jsonify((format_user(item, showCoins))), 200)


@app.route("/get_username", methods=["POST"])
def request_get_username():
    """request_get_username() (called from flask) -> Flask setup and logic for get_username()"""
    req = request.get_json()
    token = req.get("token")
    if token is None:  # Check if there was a submitted token
        return make_response(jsonify({"response": "You must submit a token!"}), 400)
    else:  # If there was a submitted token

        # First, check if there is a user with this token
        connect()
        cursor.execute("SELECT name FROM users WHERE token = ?", (token,))
        count = 0
        for _ in cursor:
            count += 1
        disconnect()

        if count > 0:  # If a user exists, return the username
            return make_response(jsonify({"username": get_username(token), "token": token}), 200)
        else:  # If a user doesn't exist with the token, it's an invalid token
            return make_response(jsonify({"response": "Invalid Token"}), 400)


@app.route("/is_forum", methods=["GET"])
def request_is_forum():
    user = request.args.get("user")
    return make_response(str(is_forum(user)).lower(), 200)


@app.route("/get_forums", methods=["GET"])
def request_get_forums():
    return make_response(json.dumps(get_forum_names()), 200)


@app.route("/is_aopscoin_admin", methods=["GET"])
def request_is_admin():
    user = request.args.get("user")
    return make_response(str(is_admin(user)).lower(), 200)


@app.route("/admin/make_admin", methods=["POST"])
def request_make_admin():
    req = request.get_json()
    token = req.get("token")
    user = req.get("user")
    if get_username(token) in ["AoPSCoin Central Bank", "casi"]:
        return make_response(make_admin(user), 200)
    else:
        return make_response("Invalid permissions", 200)


@app.route("/forum_history", methods=["GET"])
def request_forum_history():
    forum = request.args.get("forum")
    data = get_scores(forum)
    dates = []
    scores = []
    if len(data.keys()) == 0:
        return make_response("", 200)
    else:
        for key in data.keys():
            keyDate = datetime.strptime(key, "%Y-%m-%d %H:%M:%S.%f")
            keyDate = keyDate.strftime("%B%e")
            dates.append(keyDate)

            scores.append(int(data[key]) * 15)
        plt.plot(dates, scores)
        f = tempfile.TemporaryFile()
        plt.savefig(f)  # File position is at the end of the file.
        f.seek(0)
        response = send_file(io.BytesIO(f.read()), mimetype='image/png')
        f.close()
        plt.close()
        return response


@app.route("/stocks", methods=["GET"])
def request_stocks():
    """stocks() (called from flask) -> Returns dictionary of forum names mapped to forum scores.
    Uses custom scraper, which has sensitive passwords so is unfortunately not open source.
    In v1.2 this will be the stock hub."""
    return jsonify(scraper.get_forums())


@app.route("/forum_score", methods=["GET", "POST"])
def request_forum_score():
    """forum_score() (called from flask) -> Takes param argument forum. Returns score of forum."""
    forum_name = request.args.get("forum")
    return make_response(str(forum_score(forum_name)), 200)


@app.route("/admin/add_forum", methods=["POST"])
def request_add_forum():
    req = request.get_json()
    token = req.get("token")
    forum = req.get("forum")
    admins = req.get("admins")
    user = get_username(token)
    return make_response(add_forum(user, forum, admins))


@app.route("/read_transaction", methods=["POST"])
def request_read_transaction():
    """read_transaction() (called from flask) -> Takes POST argument id. Sets transaction with id id to read"""
    req = request.get_json()
    transaction = req.get("id")
    token = req.get("token")
    username = get_username(token)
    connect()
    cursor.execute("UPDATE transactions SET readByUser = 1 WHERE id = ? AND toUser = ?",
                   (transaction, username))
    disconnect()
    return make_response("Set transaction " + str(transaction) + " to read", 200)


@app.route("/get_transactions", methods=["POST"])
def request_get_transactions():
    """get_transactions() (called from flask) -> Takes POST argument token. Returns JSON of all transactions of user
    with token token """
    req = request.get_json()
    name = get_username(req.get("token"))
    connect()
    transactions = []
    if name:
        cursor.execute("SELECT * FROM transactions WHERE fromUser = ?", (name,))

        # Go through every sent transaction
        for sentTransaction in cursor:
            if format_transaction(sentTransaction, False, name)["notes"] != "Account removal":
                transactions.append(format_transaction(sentTransaction, False, name))
        cursor.execute("SELECT * FROM transactions WHERE toUser = ?", (name,))

        # Go through every received transaction
        for receivedTransaction in cursor:
            transactions.append(format_transaction(receivedTransaction, True, name))
        disconnect()

        return make_response(jsonify(transactions), 200)
    else:
        return make_response("You must submit a user", 400)


@app.route("/transfer", methods=["POST"])
def request_transfer():
    """transfer() (called from flask) -> Flask setup and logic for make_transfer(). Returns confirmatory or error
    message in HTTP Response """
    # Get response data
    req = request.get_json()
    fromUser = get_username(req.get("token"))
    toUsers = req.get("toUsers")
    amount = int(req.get("amount"))
    notes = html.escape(req.get("notes"))

    # Make the transfer and return it as an HTTP Response
    return make_response(transfer(fromUser, toUsers, amount, notes))


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


# User itself
def get_users():
    """get_users() -> Fetch all users in the database"""
    connect()  # Connect
    cursor.execute("SELECT * FROM users")  # Select all users
    item = cursor.fetchall()
    users = []
    for user in item:
        users.append(format_user(user))  # Format the users
    disconnect()
    return users


def format_user(user, showCoins=False):
    """format_user(user, showCoins=False) -> Returns {"id": user_id, "name": name, "balance": balance, "joinTime":
    joinTime, "isValid": isValid} with the necessary information. If showCoins is True, then balance is a list of all
    serial numbers. """
    user_id = user[0]
    name = user[1]
    balance = json.loads(user[2])
    if not showCoins:
        balance = len(balance)
    joinTime = user[3]
    isValid = user[4]
    isAdmin = user[5]
    return {"id": user_id, "name": name, "balance": balance, "joinTime": joinTime, "isValid": isValid,
            "isAdmin": isAdmin}


def user_in_database(name):
    """user_in_database(user) -> Returns True if user is in database, False if user is not"""
    connect()
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    item = cursor.fetchone()
    disconnect()
    if item:
        return True
    else:
        return False


# Username


def get_username(token):
    """get_username(token) -> Returns username from token"""
    if token is None:  # Make sure the token exists
        return "You must provide a Token"
    else:  # If the token exists
        # Grab the user
        connect()
        cursor.execute("SELECT name FROM users WHERE token = ?", (token,))
        item = cursor.fetchone()[0]
        disconnect()
        if item:  # If the user exists, return the username
            return item
        else:  # If the user doesn't exist, then the token is invalid
            return "Invalid Token"


# Balance
def get_balance(name):  # Get balance of user
    """get_balance(user) -> Returns balance of user"""
    connect()
    # Take the coins
    cursor.execute("SELECT coins FROM users WHERE name = ?", (name,))
    for item in cursor:
        return len(json.loads(item[0]))  # Return the length of the list
    disconnect()


def set_balance(name, balance):  # Get balance of user
    """set_balance(user,balance) -> Sets balance of user to balance by sending AoPSCoin from the Central Bank"""
    transfer("AoPSCoin Central Bank", [name], balance, "Automatic Transaction")


# Token


def get_token(name):
    """get_token(user) -> Returns token of user"""
    if user_in_database(name):  # If the user exists
        connect()
        cursor.execute("SELECT token FROM users WHERE name = ?", (name,))  # Grab the token
        for item in cursor:
            token = item[0]  # Take item
            if token == 'BLANK':  # The token is automatically blank, so we have to randomize it
                connect()
                newToken = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                cursor.execute("UPDATE users SET token = ? WHERE name = ?", (newToken, name))
                disconnect()
                emaildata.email("The token of " + name + " is " + newToken)  # Log
                return newToken
            else:  # If the user exists
                emaildata.email("The token of " + name + " is " + token)
                return token
        disconnect()
    else:  # If the user doesn't exist
        new_user(name)  # Create the user
        return get_token(name)  # Recursion!!!


def set_token(name, token):
    """set_token(user,token) -> Sets token of user to token"""
    connect()
    cursor.execute("UPDATE users SET token = ? WHERE name = ?", (token, name))
    print("Set " + name + "'s token as " + token)
    disconnect()


# Admin Check


def user_is_admin(name):
    return name in get_admins() + get_forum_names() + get_forum_admins()


def is_forum(name):
    return name in get_forum_names()


# Create/Delete
def new_user(name):
    """new_user(user) -> Adds user with name name to database. User starts with 0 coins."""
    if user_in_database(name):
        return "User already exists"
    else:
        connect()
        coins = json.dumps([])  # No coins (yet)
        cursor.execute('INSERT INTO users (name,coins) VALUES (?,?)', (name, coins))
        disconnect()
        return "User " + name + " created"


def delete_user(name):
    """delete_user(user) -> Deletes user user from database. Only accessible from command line"""
    if name == "casi" or name == "AoPSCoin Central Bank":  # No deleting important accounts
        raise Exception("Error in main.py, line 4: No module Flask")  # :P
    elif user_in_database(name):  # If the user exists
        validate(name)  # Make the user valid so it can transfer AoPSCoin to the central bank
        validate("AoPSCoin Central Bank")  # Make sure the central bank is valid
        transfer(name, "AoPSCoin Central Bank", get_balance(name),
                 "Account removal")  # Transfer all the user's AoPSCoin to the Central Bank
        connect()
        cursor.execute('DELETE FROM users WHERE name = ?', (name,))  # Remove the user from database
        print("User " + name + " deleted")
        disconnect()
    else:
        print("No such user")


# Validity

def is_valid(name):
    """is_valid(user) -> Returns bool for whether user is valid"""
    connect()
    cursor.execute("SELECT isValid FROM users WHERE name = ?", (name,))
    item = cursor.fetchone()
    disconnect()
    item = item[0]
    return item == 1


def invalidate(name):
    """invalidate(user) -> Invalidates user. Invalid users cannot send or receive AoPSCoin"""
    connect()
    cursor.execute("UPDATE users SET isValid = 0 WHERE name = ?", (name,))
    disconnect()


def validate(name):
    """validate(user) -> Validates user."""
    connect()
    cursor.execute("UPDATE users SET isValid = 1 WHERE name = ?", (name,))
    disconnect()


# Administrative Privileges


def make_admin(name):
    new_user(name)
    connect()
    cursor.execute("UPDATE users SET isAdmin = 1 WHERE name = ?", (name,))
    disconnect()
    return "Made " + name + " admin"


def make_normal_user(name):
    new_user(name)
    connect()
    cursor.execute("UPDATE users SET isAdmin = 0 WHERE name = ?", (name,))
    disconnect()


def is_admin(name):
    connect()
    cursor.execute("SELECT isAdmin FROM users WHERE name = ?", (name,))
    item = cursor.fetchone()
    disconnect()
    item = item[0]
    return item == 1


# ------------------------------------------
# Functions for the Admin Toolbox


def get_scores(forum):
    data = recorder.get()
    finalData = {}
    for key in data.keys():
        snapshot = data[key]
        for item in snapshot:
            if item["item_text"] == forum:
                finalData[key] = item["item_score"]
    return finalData


# ------------------------------------------
# Functions for Rankings/Stocks


def forum_score(name):
    forums = scraper.get_forums()
    score = 0
    for forum in forums:
        if forum["name"] == name:
            score = forum["score"]
    return int(score)


def most_recent_balance(name):
    if forum_in_database(name):  # If the user exists
        connect()
        cursor.execute("SELECT lastBalance FROM forums WHERE name = ?", (name,))  # Grab the token
        balance = cursor.fetchone()
        disconnect()
        return balance[0]
    else:  # If the forum doesn't exist
        return 0


def update_most_recent_balance(name, balance):
    connect()
    cursor.execute("UPDATE forums SET lastBalance = ? WHERE name = ?", (balance, name))  # Grab the token
    disconnect()
    print("Updated balance")


# ------------------------------------------
# Functions for Admins


def add_forum(user_name, forum_name, admins):
    if is_admin(user_name):
        return new_forum(forum_name, admins)
    else:
        return "You are not a valid admin."


def get_forum_admins():
    connect()
    cursor.execute("SELECT * FROM forums")
    forums = cursor.fetchall()
    admins = []
    for forum in forums:
        for admin in json.loads(forum[2]):
            admins.append(admin)
    return admins


def get_admins():
    connect()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    admins = []
    for user in users:
        if user[5] == 1:
            admins.append(user[1])
    return admins


# ------------------------------------------
# Functions for Forums

def get_forum_names():
    forumNames = []
    connect()
    cursor.execute("SELECT * FROM forums")
    forums = cursor.fetchall()
    for forum in forums:
        forumNames.append(forum[1])
    return forumNames


def new_forum(name, admins):
    """new_user(user) -> Adds user with name name to database. User starts with 0 coins."""
    if forum_in_database(name):
        return "Forum already exists"
    else:
        connect()
        admins = json.dumps(admins)
        owners = json.dumps({name: 100})  # All forums start with 100% of their ownership in the forum account
        cursor.execute('INSERT INTO forums (name,admins, owners) VALUES (?,?,?)', (name, admins, owners))
        disconnect()
        return "Forum " + name + " added to database"


def forum_in_database(name):
    """user_in_database(user) -> Returns True if user is in database, False if user is not"""
    connect()
    cursor.execute("SELECT * FROM forums WHERE name = ?", (name,))
    item = cursor.fetchone()
    disconnect()
    if item:
        return True
    else:
        return False


def format_forum(forum):
    return {"id": forum[0], "name": forum[1], "admins": json.loads(forum[2]), "owners": json.loads(forum[3]),
            "deservedCoins": int(forum[4]), "joinTime": forum[5]}


# ------------------------------------------
# Functions for Transactions


def new_transaction(fromUser, toUser, coins, notes):
    """new_transaction(fromUser, toUser, coins, notes) -> Creates new transaction with (fromUser, toUser, coins,
    notes) """
    connect()
    cursor.execute('INSERT INTO transactions (fromUser,toUser,coins,notes) VALUES (?,?,?,?)',
                   (fromUser, toUser, json.dumps(coins), notes))
    email_transaction([fromUser, toUser, coins, html.unescape(notes)])
    disconnect()


def format_transaction(transaction, received, name):
    """format_transaction(transaction, received, username) -> {"id": ID, "name": name, "amount": amount, "received":
    received, "notes": notes, "transferTime": transferTime, "readByUser": readByUser}
    """
    ID = transaction[0]
    fromUser = transaction[1]
    toUser = transaction[2]
    if fromUser == name:
        name = toUser
    elif toUser == name:
        name = fromUser
    amount = len(json.loads(transaction[3]))
    notes = transaction[4]
    transferTime = transaction[5]
    readByUser = transaction[7]
    return {"id": ID, "name": name, "amount": amount, "received": received, "notes": notes,
            "transferTime": transferTime, "readByUser": readByUser}


def email_transaction(transaction):
    """email_transaction(transaction) -> Emails transaction from aopscoin@gmail.com to aopscoinmanager@gmail.com
    emaildata is a custom module which unfortunately has sensitive passwords"""
    emaildata.email(transaction)


# ------------------------------------------
# Transfer Function


def transfer(fromUser, toUsers, amount, notes=""):
    """make_transfer(fromUser, toUsers, amount, notes) -> String(confirmation/error),
    transfers amount AoPSCoins from fromUser to each user in toUsers. Optional notes"""
    if amount < 1:
        return "You must send at least 1 AoPSCoin!"
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
            if get_balance(fromUser) >= amount * len(to):  # Check that the sending user has enough money
                for toUser in to:  # Every valid user
                    coins = take_coins(fromUser, amount)  # Take the coins
                    give_coins(toUser, coins)  # Give to the recipient
                    new_transaction(fromUser, toUser, coins, notes)  # Add the transaction
                response = ""
                if len(to) > 0:
                    # Example Response -> Successfully transferred 10 AoPSCoins from AoPSCoin Central Bank to casi,
                    # rrusczyk
                    response += "Successfully transferred " + str(
                        amount) + " AoPSCoins from " + fromUser + " to " + ', '.join(to) + ". "
                if len(inValid) > 0:
                    # Example -> The following users were invalid: casi, RYang2
                    response += "The following users were invalid: " + ', '.join(inValid)
                return response

            else:
                return "Not enough money!"  # Not enough money


def take_coins(user, amount):
    """take_coins(user, amount) -> Removes amount coins from user, and returns them in a list"""
    connect()
    cursor.execute("SELECT coins FROM users WHERE name = ?", (user,))  # Get the coins by the username
    coins = json.loads(cursor.fetchall()[0][0])  # Pluck out the JSON with indexes and convert to list
    cursor.execute("UPDATE users SET coins = ? WHERE name = ?", (json.dumps(coins[amount:]), user))
    disconnect()
    return coins[:amount]


def give_coins(user, coins):
    """give_coins(user, coins) -> Adds every coin in coins to user's coin list"""
    connect()
    cursor.execute("SELECT coins FROM users WHERE name = ?", (user,))  # Get the coins by the username
    originalCoins = json.loads(cursor.fetchall()[0][0])  # Pluck out the JSON with indexes and convert to list
    for coin in coins:
        originalCoins.append(coin)  # Add the new coins
    cursor.execute("UPDATE users SET coins = ? WHERE name = ?",
                   (json.dumps(originalCoins), user))  # Set the user's coins as the updated coin set
    disconnect()


if __name__ == "__main__":
    app.run(host='0.0.0.0')
