# import necessary libraries
import pandas as pd
import numpy as np
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, desc

from flask import (
    Flask,
    render_template,
    jsonify)

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///DataSets/belly_button_biodiversity.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
Base.classes.keys()

# Save references to the table
Samples = Base.classes.samples
OTU = Base.classes.otu
Samples_Metadata = Base.classes.samples_metadata

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


# Flask Routes
# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# List of Sample Names
@app.route('/names')
def names():
    samples_stmt = session.query(Samples).statement
    samples_df = pd.read_sql_query(samples_stmt, session.bind)
    samples_df.set_index("otu_id", inplace = True)
    return jsonify(list(samples_df.columns))

# List of OTU Descriptions 
@app.route('/otu')
def otu_descriptions():
    otu_stmt = session.query(OTU).statement
    otu_df = pd.read_sql_query(otu_stmt, session.bind)
    otu_df.set_index("otu_id", inplace=True)
    otu_descriptions = list(otu_df.lowest_taxonomic_unit_found)
    return jsonify(otu_descriptions)

# MetaData for a given sample
@app.route('/metadata/<sample>')
def metadata(sample):   
    
    # Grabbing input
    sample_id = int(sample[3:])  

    # Creating an empty dictionary for the data  
    sample_metadata = {}
    
    # Grab metadata table
    results = session.query(Samples_Metadata)
    
    # Loop through query & add info to dictionary
    for result in results:
        if (sample_id == result.SAMPLEID):
            sample_metadata["AGE"] = result.AGE
            sample_metadata["BBTYPE"] = result.BBTYPE
            sample_metadata["ETHNICITY"] = result.ETHNICITY
            sample_metadata["GENDER"] = result.GENDER
            sample_metadata["LOCATION"] = result.LOCATION
            sample_metadata["SAMPLEID"] = result.SAMPLEID
    return jsonify(sample_metadata)

# Weekly Washing Frequency
@app.route('/wfreq/<sample>')
def wfreq(sample):

    # Grabbing input
    sample_id = int(sample[3:])

    # Grab metadata table
    results = session.query(Samples_Metadata)

    #Loop through query & grab wfreq
    for result in results:
        if sample_id == result.SAMPLEID:
            wfreq = result.WFREQ
    return jsonify(wfreq)

# OTU IDs and SAMPLE Values 
@app.route("/samples/<sample>")
def samples(sample):

    # Grab info
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)
    
    # Make sure sample was found in the columns
    if sample not in df.columns:
        return jsonify(f"Error Sample: {sample} not found!")
    
    # Return any sample values greater than 1
    df = df[df[sample] > 1]

    # Sort the results by sample in descending order
    df = df.sort_values(by=sample, ascending=0)

    # Format the data to send as json
    data = [{
        "otu_ids": df[sample].index.values.tolist(),
        "sample_values": df[sample].values.tolist()
    }]
    return jsonify(data)

# Initiate Flask app
if __name__ == "__main__":
    app.run(debug=True)