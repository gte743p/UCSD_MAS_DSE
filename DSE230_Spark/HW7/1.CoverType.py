# Name: Josh Wilson
# Email: jsw037@eng.ucsd.edu
# PID: A53228518

from pyspark import SparkContext
sc = SparkContext()

# Your program here
from pyspark.mllib.linalg import Vectors
from pyspark.mllib.regression import LabeledPoint

from string import split,strip

from pyspark.mllib.tree import GradientBoostedTrees, GradientBoostedTreesModel, RandomForest
from pyspark.mllib.util import MLUtils


# ### Cover Type
# 
# Classify geographical locations according to their predicted tree cover:
# 
# * **URL:** http://archive.ics.uci.edu/ml/datasets/Covertype
# * **Abstract:** Forest CoverType dataset
# * **Data Set Description:** http://archive.ics.uci.edu/ml/machine-learning-databases/covtype/covtype.info

#define a dictionary of cover types
CoverTypes={1.0: 'Spruce/Fir',
            2.0: 'Lodgepole Pine',
            3.0: 'Ponderosa Pine',
            4.0: 'Cottonwood/Willow',
            5.0: 'Aspen',
            6.0: 'Douglas-fir',
            7.0: 'Krummholz' }

# Define the feature names
cols_txt="""
Elevation, Aspect, Slope, Horizontal_Distance_To_Hydrology,
Vertical_Distance_To_Hydrology, Horizontal_Distance_To_Roadways,
Hillshade_9am, Hillshade_Noon, Hillshade_3pm,
Horizontal_Distance_To_Fire_Points, Wilderness_Area (4 binarycolumns), 
Soil_Type (40 binary columns), Cover_Type
"""

# Break up features that are made out of several binary features.
from string import split,strip
cols=[strip(a) for a in split(cols_txt,',')]
colDict={a:[a] for a in cols}
colDict['Soil_Type (40 binary columns)'] = ['ST_'+str(i) for i in range(40)]
colDict['Wilderness_Area (4 binarycolumns)'] = ['WA_'+str(i) for i in range(4)]
Columns=[]
for item in cols:
    Columns=Columns+colDict[item]

# Read the file into an RDD
# If doing this on a real cluster, you need the file to be available on all nodes, ideally in HDFS.
path='/covtype/covtype.data'
inputRDD=sc.textFile(path)

# ### Making the problem binary
# 
# The implementation of BoostedGradientTrees in MLLib supports only binary problems. the `CovTYpe` problem has
# 7 classes. To make the problem binary we choose the `Lodgepole Pine` (label = 2.0). We therefor transform the dataset to a new dataset where the label is `1.0` is the class is `Lodgepole Pine` and is `0.0` otherwise.

# helper function to create LabeledPoint with binarized labels
def binarize_labels(line,tgt):
    lbl = line[-1:][0]
    data = line[:-1]
    if lbl == tgt:
        return LabeledPoint(1.0, data)
    else:
        return LabeledPoint(0.0, data)

# binarize labels
Label=2.0
Data=inputRDD.map(lambda line: [float(x) for x in line.split(',')]).map(lambda V:binarize_labels(V,Label))

# full dataset for cluster
(trainingData,testData)=Data.randomSplit([0.7,0.3],seed=255)

# subset of dataset for local testing
#Data1=Data.sample(False,0.5).cache()
#(trainingData,testData)=Data1.randomSplit([0.7,0.3])

# ### Gradient Boosted Tree Model
errors={}
for depth in [10]:
    model=GradientBoostedTrees.trainClassifier(trainingData, categoricalFeaturesInfo={}, 
                                               numIterations=25, maxDepth=depth,
                                               learningRate=0.25)
    errors[depth]={}
    dataSets={'train':trainingData,'test':testData}
    for name in dataSets.keys():  # Calculate errors on train and test sets
        data=dataSets[name]
        Predicted=model.predict(data.map(lambda x: x.features))
        LabelsAndPredictions=data.map(lambda LP: LP.label).zip(Predicted)
        Err = LabelsAndPredictions.filter(lambda (v,p):v != p).count()/float(data.count())
        errors[depth][name]=Err
    print depth,errors[depth]