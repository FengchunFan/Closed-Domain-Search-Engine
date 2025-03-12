#file modified based on the sample provided by Mr.SHIHAB RASHID from CS172 in UC riverside
#export FLASK_APP = interface
#flask run -h 0.0.0.0 -p 8888

from flask import Flask, render_template, send_from_directory, request

app = Flask(__name__) #instance of flask class

#@app.route("/") #root url
#def main():
#    return render_template("input.html")

@app.route('/', methods = ['POST', 'GET'])
def input():
    return render_template('input.html')

@app.route('/output', methods = ['POST', 'GET'])
def output():
    if request.method == 'GET':
        return f"Nothing"
    if request.method == 'POST':
        form_data = request.form
        query = form_data['query']
        print(f"this is the query: {query}")
        return render_template('output.html')

#@app.route("/output0.csv")
@app.route("/result.csv")
def retrieve_result():
    #return send_from_directory("static", "output0.csv")
    return send_from_directory("static", "result.csv")

if __name__ == "__main__":
    app.run(debug=True)