# parkingapp_sample/app.py

from __init__ import create_app

app = create_app()

if __name__ == "__main__":
    # Run on 127.0.0.1:5000 by default
    app.run(debug=True)

 

