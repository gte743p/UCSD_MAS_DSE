===========================
DSE_capstone PROJECT_README
===========================

Overview
========

This is the README for the UCSD DSE capstone project for Team 3 "Drive Classy, San Diego".

The goal of the project is to use congestion data from a popular traffic sharing app to explore
patterns and predict traffic behavior in San Diego. This code deals specifically with
selecting which street segments and time windows to use in the analysis, clustering of that data
and modeling the traffic to predict future traffic levels. A challenge for this project was the fact that the
source data only provided positive results, meaning data was only recorded when traffic congestion was encountered
by app users. This resulted in a highly skewed data set.

The project also consists of SQL code and notebooks to create the required database tables, python files containing helper functions,
and several `Jupyter <http://jupyter.org/>`_ notebooks that process the data, train the models and make traffic predictions.

Workflow
========

There are several steps needed to analyze existing traffic data and make predictions:

    1.  Create the database in PostgreSQL and enable the PostGIS extension.

    2.  Load the raw data from the source csv file into the database. This step is accomplished with the
        Data Transformation notebook. The source data was divided into congestion events defined by a unique ID that
        could include data from arbitrary spatial line segments (defined as a PolyLine Geom feature with 2 or more
        latitude/longitude pairs). To enhance the format of the data for modeling, the team decided to break up the
        original congestion event data into a matrix consisting of unique line segments of a single lat/lon pair and
        all possible time windows during the data sampling period. Time segments were broken up in 2 ways:

            a.  A single contiguous index of all time windows across the entire sample period.

            b.  Aggregate the time windows into unique Time of day and Day of Week groups (e.g. Monday at 4pm)
                across the entire sample period.

        The code allows for modeling on both of these Time segments groupings.

        The user can also create all required database tables by running the SQL creation file. Once the tables
        are created, other features such as local events (e.g. concert, Farmer's Markets, etc) and Padres games
        can be loaded into the database for use during the exploration and modeling phases.

    3.  Run the Data Exploration notebook to view distribution of features and the effect of combining the data points
        into time windows of various sizes.

    4.  Run the Step 1 notebook to create the data needed for modeling. This step includes clustering the data with
        any of several clustering algorithms and optionally including events and Padres games. The entire process
        of preparing the data and producing the models is controlled by an args file that contains setting to
        tell the code what to do. This allows easy tracking of the inputs used to produce a particular output.
        Cluster data is saved via standard Python `pickle <https://docs.python.org/2/library/pickle.html/>`_ files.

        Data can be unskewed to a given negative to positive ratio via args file parameters.

    5.  Run the Step 2 notebook to train the several baseline models and use an automated `tool <https://epistasislab.github.io/tpot/>`_
        to find the best model and paremeters for the full data set and for each cluster. This tool is controlled
        by a python dictionary that provides input parameters to guide the tool in its optimization process.
        These models are also saved to pickle files for later use predicting traffic for new data.

        The modeling is done in 2 stages:

        Stage 1.    Produce a binary value that predicts if there will be traffic for a given segment and datetime.

        Stage 2.    Predict the level of traffic (classification levels 1 through 5) for all segments and datetimes
                    that were predicted to have traffic in Stage 1.

    6.  Run the Step 3 notebook to create predictions for segments and datetimes that are either new data or that were
        held out of the model training and validation process.

    7.  Create tables showing accuracy metrics via a notebook to evaluate the performance of various modeling efforts.

    8.  Produce a geojson file for use by the map visualization tool.



The programs are written in `Python 2.7 <https://docs.python.org/2/index.html>`_, and
`PostgreSQL <https://www.postgresql.org>`_,was used as the database along with the `PostGIS <https://postgis.net>`_
spatial extensions.  Documentation was created using `Sphinx <http://www.sphinx-doc.org/en/stable/>`_.
Version control was stored in `Git <https://git-scm.com/>`_ repository on `github
<https://github.com/mas-dse/capstone-cohort3-group3>`_.
