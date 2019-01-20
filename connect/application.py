import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from pytz import timezone
from helpers import apology, login_required, lookup, usd


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("postgres://oxrzgukfhlkdxn:c8bdba933daf90ba9933e69d81c7c41948e86b5719bc3a3e0a3bcacd35e6f789@ec2-54-235-77-0.compute-1.amazonaws.com:5432/d582r814ff2gbp
")

# Convert a string value to a time value
def convert(timeString):
    time = timeString.split(":")
    minute = int(time[0])*60 + int(time[1])
    return minute

# The default time shown is current time plus one hour
def showtime():
    now = datetime.datetime.now(timezone('US/Eastern'))
    ahead = now + datetime.timedelta(hours=1)
    return ahead.strftime("%H:%M")

@app.route("/", methods=["GET", "POST"])
def index():
    # POST
    if request.method == "POST":
        # Validate form submission
        if not request.form.get("name"):
            return apology("Name is required")
        elif not request.form.get("time"):
            return apology("Expiration time is required")
        # Validate time (must be after current time)
        now = datetime.datetime.now(timezone('US/Eastern'))
        # Format time
        current = f"{now.hour}:{now.minute}"
        # Validate time
        if (convert(request.form.get("time")) < convert(current)):
            return apology("Must enter time after current")
        else:
            flash("Checked-In!")

        # Enter submission into database
        db.execute("INSERT INTO 'Users' ('name','time','location','interests') VALUES(:name, :time, :location, :interests)",
                    name=request.form.get("name"), time=request.form.get("time"), location=request.form.get("location"), interests=request.form.get("interests"))
        # Sort rows by oldest time first
        rows = db.execute("SELECT * FROM Users ORDER BY time ASC")
        # Return to homepage after sorting
        return redirect("/")


    # GET
    else:
        # Get rows from database and sort users by time leaving
        rows = db.execute("SELECT * FROM Users ORDER BY time ASC")

        # Compare times and delete rows with expired times
        now = datetime.datetime.now(timezone('US/Eastern'))
        current = f"{now.hour}:{now.minute}"
        rows = db.execute("SELECT * FROM Users")

        for row in rows:
            # Delete entries that have invalid times
            if convert(row["time"]) < convert(current):
                db.execute("DELETE FROM Users WHERE id=:id", id=row['id'])
        # Get rows from database and sort users by time leaving
        rows = db.execute("SELECT * FROM Users ORDER BY time ASC")
        # Render user list
        return render_template("index.html", rows=rows, prefill=None, showtime=showtime())

# Delete entry function
@app.route("/delete/<int:id>")
def delete(id):
    db.execute("DELETE FROM Users WHERE id=:id", id=id)
    # Get rows from database and sort users by time leaving
    rows = db.execute("SELECT * FROM Users ORDER BY time ASC")
    return redirect("/")

# Edit entry function
@app.route("/edit/<int:line>")
def edit(line):
    # Query row from database
    row = db.execute("SELECT * FROM Users WHERE id=:line", line=line)
    # Remove row from database
    db.execute("DELETE FROM Users WHERE id=:line", line=line)
	# Get rows from database and sort users by time leaving
    rows = db.execute("SELECT * FROM Users ORDER BY time ASC")

    # Render index.html with form fields pre-populated from the deleted row  -- how prepopulate?
    return render_template("index.html", prefill=row[0], rows=rows)
