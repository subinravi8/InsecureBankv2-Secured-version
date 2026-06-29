import getopt
import web
import sys
from cheroot import wsgi 
from flask import Flask, request, jsonify
from functools import wraps
from models import User, Account  # FIXED: Removed the '.' before models
from database import db_session  # FIXED: Removed the '.' before database
import simplejson as json

makejson = json.dumps
app = Flask(__name__)

DEFAULT_PORT_NO = 8888

def usageguide():
    print("InsecureBankv2 Backend-Server")
    print("Options: ")
    print("  --port p    serve on port p (default 8888)")
    print("  --help      print this message")

@app.errorhandler(500)
def internal_servererror(error):
    print(" [!]", error)
    return "Internal Server Error", 500

'''
The function handles the authentication mechanism
'''
@app.route('/login', methods=['POST'])
def login():
    Responsemsg = "fail"
    user = request.form['username']
    u = User.query.filter(User.username == request.form["username"]).first()
    print("u=", u)
    
    # FIXED: Proper indentation for if/elif/else
    if u and u.password == request.form["password"]:
        Responsemsg = "Correct Credentials"
    elif u and u.password != request.form["password"]:
        Responsemsg = "Wrong Password"
    elif not u:
        Responsemsg = "User Does not Exist"
    else:
        Responsemsg = "Some Error"
        
    data = {"message": Responsemsg, "user": user}
    print(makejson(data))
    return makejson(data)

'''
The function responds back with the from and to debit accounts corresponding to logged in user
'''
@app.route('/getaccounts', methods=['POST'])
def getaccounts():
    Responsemsg = "fail"
    acc1 = acc2 = from_acc = to_acc = 0
    user = request.form['username']
    u = User.query.filter(User.username == user).first()
    
    if not u or u.password != request.form["password"]:
        Responsemsg = "Wrong Credentials so trx fail"
    else:
        Responsemsg = "Correct Credentials so get accounts will continue"
        a = Account.query.filter(Account.user == user)
        
        # FIXED: Proper indentation for the loops and if statements
        for i in a:
            if (i.type == 'from'):
                from_acc = i.account_number
            for j in a:
                if (i.type == 'to'):
                    to_acc = i.account_number
                    
    data = {"message": Responsemsg, "from": from_acc, "to": to_acc}
    print(makejson(data))
    return makejson(data)

'''
The function takes a new password as input and passes it on to the change password module
'''
@app.route('/changepassword', methods=['POST'])
def changePassword():
    user = request.form.get('username')
    old_pass = request.form.get('oldPassword')
    new_pass = request.form.get('newpassword')
    
    if not user or not old_pass or not new_pass:
        return jsonify({"message": "Missing required fields", "status": "failed"}), 400
    
    u = User.query.filter(User.username == user).first()
    if not u:
        return jsonify({"message": "User does not exist", "status": "failed"}), 404
    
    if u.password != old_pass:
        return jsonify({"message": "Incorrect current password", "status": "failed"}), 401
    
    u.password = new_pass
    db_session.commit()
    return jsonify({"message": "Password changed successfully", "status": "success"}), 200
'''
The function handles the transaction module
'''
@app.route('/dotransfer', methods=['POST'])
def dotransfer():
    user = request.form['username']
    password = request.form['password']
    from_acc = request.form['from_acc']
    to_acc = request.form['to_acc']
    amount_str = request.form['amount']
    
    # 1. Validate credentials
    u = User.query.filter(User.username == user).first()
    if not u or u.password != password:
        return jsonify({"message": "Invalid credentials", "status": "failed"})
    
    # 2. Validate ownership of source account (KILLS IDOR)
    account = Account.query.filter(Account.account_number == from_acc, Account.user == user).first()
    if not account:
        return jsonify({"message": "Invalid transaction request", "status": "failed"})
    
    # 3. Fetch the actual account objects for both accounts
    from_account = Account.query.filter(Account.account_number == from_acc).first()
    to_account = Account.query.filter(Account.account_number == to_acc).first()
    
    # 4. Validate that BOTH accounts exist in the system
    if not from_account or not to_account:
        return jsonify({"message": "Invalid accounts provided", "status": "failed"})
    
    # 5. Check sufficient balance
    if from_account.balance < int(amount_str):
        return jsonify({"message": "Insufficient balance", "status": "failed"})
    
    # 6. Perform the transfer
    from_account.balance -= int(amount_str)
    to_account.balance += int(amount_str)
    db_session.commit()
    
    return jsonify({"message": "Success", "from": from_acc, "to": to_acc, "amount": amount_str})
'''
The function provides login mechanism to a developer user during development phase
'''
@app.route('/devlogin', methods=['POST'])
def devlogin():
    user = request.form['username']
    Responsemsg = "Correct Credentials"
    data = {"message": Responsemsg, "user": user}
    print(makejson(data))
    return makejson(data)

if __name__ == '__main__':
    port = DEFAULT_PORT_NO
    options, args = getopt.getopt(sys.argv[1:], "", ["help", "port="])
    
    # FIXED: Proper indentation for the for loop and if/elif statements
    for op, arg1 in options:
        if op == "--help":
            usageguide()
            sys.exit(2)
        elif op == "--port":
            port = int(arg1)

    urls = ("/.*", "app")
    apps = web.application(urls, globals())
    server = wsgi.Server(("0.0.0.0", port), app, server_name='localhost')
    print("The server is hosted on port:", (port))
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
