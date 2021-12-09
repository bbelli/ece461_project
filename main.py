from flask import Flask, render_template, redirect, url_for, request, session
from flask_executor import Executor
from storage import uploadFiles,downloadFiles
from sqlconnector import connect
import base64
import pandas as pd
import json
from helper import *


app = Flask(__name__)
executor = Executor(app)
cnx = connect()
if not cnx:
    exit("Error connecting to database")

@app.route('/packages/',defaults = {'offset' : 1})
@app.route('/packages/<int:offset>',methods = ['GET']) #essential
def getPackages(offset):
    cursor = cnx.cursor(buffered = True)
    query = "SELECT * FROM package ORDER BY id LIMIT %s,10;"
    cursor.execute(query,((offset-1)*10 if offset > 0 else 0,))
    resp = pd.DataFrame(cursor.fetchall())
    cnx.commit()
    resp.columns = cursor.column_names
    resp = resp.to_json(orient='records')
    cursor.close()
    return resp

@app.route('/reset', methods = ['DELETE'])
def registryReset():
    cursor = cnx.cursor(buffered = True)
    query = "DELETE FROM package;"
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    return 'Reset Registry'

@app.route('/package/<id>', methods = ['DELETE']) #essential
def deletePackage(id):
    #Delete from package id
    cursor = cnx.cursor(buffered = True)
    cursor.execute("DELETE FROM package WHERE package_id = %s",(id,))
    cursor.execute("SELECT ROW_COUNT()")
    cnx.commit()
    if cursor.fetchone()[0] == 0:
        return 'Package not found', 400
    return 'Package Deleted',200

@app.route('/package/<id>', methods = ['PUT']) 
def updatePackage(id):
    #Update package
    cursor = cnx.cursor(buffered = True)
    cursor.execute("SELECT * FROM package WHERE package_id = %s",(id,))
    if cursor.rowcount == 0:
        return 'Package not found', 400
    data = request.get_json()
    query = "UPDATE package SET package_name = %s, version = %s, url = %s, jsprogram = %s  WHERE package_id = %s;"
    cursor.execute(query,(data['metadata']['Name'],data['metadata']['Version'],data['data']['URL'],data['data']['JSProgram'],id))
    cnx.commit()
    write_url(data['data']['URL'])
    run_scoring()
    with open("dict.txt") as fptr:
        dict_resp = json.loads(fptr.read())
    isIngest = ingestibilty(dict_resp)
    if (isIngest) is not True:
        cursor.close()
        return "Ingestibility failed. Package was not uploaded to database.", 403
    query = "UPDATE package SET ramp_up = %s, correctness = %s, bus_factor = %s, responsiveness = %s, license = %s, dependancy = %s, overall = %s  WHERE package_id = %s;"
    cursor.execute(query,(dict_resp['ramp_up'],dict_resp['correctness'],dict_resp['bus_factor'],dict_resp['responsiveness'],dict_resp['license'],dict_resp['dependency'],dict_resp['score'], data['metadata']['ID']))#dict_resp['correctness'],dict_resp['bus_factor'],dict_resp['responsiveness'],dict_resp['license'],dict_resp['dependency'],dict_resp['score'],id))    
    cnx.commit()
    return f'Updated package {id}',200

@app.route('/package/<id>', methods = ['GET'])
def packageRetrieve(id):
    cursor = cnx.cursor(buffered = True)
    cursor.execute("SELECT * FROM package WHERE package_id = %s",(id,))
    packageData = pd.DataFrame(cursor.fetchall())
    if packageData.empty:
        return 'Package not found', 400
    packageData.columns = cursor.column_names
    print(packageData)
    resp = packageData.to_json(orient='records')
    resp = resp[1:-1] #remove first and last element
    resp = "{" + resp + "}"
    print(resp,type(resp))
    return resp, 200

@app.route('/package', methods = ['POST']) #essential
def packageCreate():
    ''' upload file to gcp storage bucket'''
    req = request.get_json()
    if not (req and req['metadata']['Name'] and req['metadata']['Version']):
        return 'Invalid Request', 400
    cursor = cnx.cursor(buffered = True)
    #Check if package exists
    cursor.execute("SELECT * FROM package WHERE package_id = %s",(req['metadata']['ID'],))

    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO package (id, package_id, package_name, version, url, jsprogram) VALUES (id,%s,%s,%s,%s,%s)""",
                (req['metadata']['ID'],req['metadata']['Name'] , req['metadata']['Version'] , req['data']['URL'] , req['data']['JSProgram']))
        # Rate here
        write_url(req['data']['URL'])
        run_scoring()
        with open("dict.txt") as fptr:
            dict_resp = json.loads(fptr.read())
        isIngest = ingestibilty(dict_resp)
        if (isIngest) is not True:
            cursor.close()
            return "Ingestibility failed. Package was not uploaded to database.", 403
        print(isIngest)
        print(dict_resp)
    
        # cursor.execute("""
        # INSERT INTO package (ramp_up, correctness, bus_factor, responsiveness, license, dependancy, overall) VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        #         (req['metadata']['ID'],req['metadata']['Name'] , req['metadata']['Version'] , req['data']['URL'] , req['data']['JSProgram']))
        # #, correctness = %d, bus_factor = %d, responsiveness = %d, license = %d, dependancy = %d, overall = %d 
        # # cursor.execute(query,('0.0','0.0','0.0','0.0','0.0','0.0','0.0',id))
        # print(type(dict_resp['ramp_up']))
        query = "UPDATE package SET ramp_up = %s, correctness = %s, bus_factor = %s, responsiveness = %s, license = %s, dependancy = %s, overall = %s  WHERE package_id = %s;"
        cursor.execute(query,(dict_resp['ramp_up'],dict_resp['correctness'],dict_resp['bus_factor'],dict_resp['responsiveness'],dict_resp['license'],dict_resp['dependency'],dict_resp['score'], req['metadata']['ID']))#dict_resp['correctness'],dict_resp['bus_factor'],dict_resp['responsiveness'],dict_resp['license'],dict_resp['dependency'],dict_resp['score'],id))
        
        cnx.commit()
        cursor.execute("SELECT * FROM package WHERE package_id = %s",(req['metadata']['ID'],))
        resp = pd.DataFrame(cursor.fetchall())
        resp.columns = cursor.column_names
        resp = resp.to_json(orient='records')

        
        executor.submit(uploadFiles,req['metadata']['ID'],)
        return resp[1:-1], 201
    else:
        cursor.close()
        return "Package ID already exists. Choose a different ID.", 403
    #return 'Creating package'

'''
@app.before_request
def validate_token():
    print("before_request is running!")
'''


@app.route('/authenticate', methods = ['PUT']) #essential
def createAuthToken():
    try:
        user_id = request.get_json()["User"]["name"]
        pwd = request.get_json()["Secret"]["password"]
        admin = request.get_json()["User"]["isAdmin"]
        payload = {
            'sub': pwd,
            'name': user_id,
            'admin': admin
        }
        print(pwd, admin, app.config.get('SECRET_KEY') )
        code = jwt.encode(
            payload,
           'secret',
            algorithm='HS256'
        )

        return code
    except Exception as e:
        print(e)
        return e


@app.route('/package/byName/<name>', methods = ['GET'])
def getPackageByName(name):
    """
    select * from database where packageName == Name
    """
    cursor = cnx.cursor(buffered = True)
    cursor.execute("SELECT * FROM package WHERE package_name = %s",(name,))
    packageData = pd.DataFrame(cursor.fetchall())
    if packageData.empty:
        return 'Package not found', 400
    packageData.columns = cursor.column_names
    print(packageData)
    resp = packageData.to_json(orient='records')
    resp = resp[1:-1] #remove first and last element 
    resp = "{" + resp + "}"
    print(resp,type(resp))
    return resp, 200


@app.route('/package/byName/<name>', methods = ['DELETE'])
def deletePackageByName(name): #essential
    cursor = cnx.cursor(buffered = True)
    cursor.execute("DELETE FROM package WHERE package_name = %s",(name,))
    cursor.execute("SELECT ROW_COUNT()")
    cnx.commit()
    if cursor.fetchone()[0] == 0:
        return 'Package not found', 400
    return 'Package Deleted',200

@app.route('/package/<id>/rate', methods = ['GET']) #essential
def rate(id):
    
    cursor = cnx.cursor(buffered = True)
    cursor.execute(("SELECT * FROM package WHERE package_id = %s"),(id,))
    
    frame = pd.DataFrame(cursor.fetchall())
    if frame.empty:
        return 'Package not found', 400
    frame.columns = cursor.column_names
    resp = frame.to_json(orient='records')
    return resp,200
    

@app.route('/')
def root():
    # For the sake of example, use static information to inflate the template.
    # This will be replaced with real information in later steps.
    dummy_times = [datetime.datetime(2018, 1, 1, 10, 0, 0),
                   datetime.datetime(2018, 1, 2, 10, 30, 0),
                   datetime.datetime(2018, 1, 3, 11, 0, 0),
                   ]

    return render_template('index.html', times=dummy_times)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
