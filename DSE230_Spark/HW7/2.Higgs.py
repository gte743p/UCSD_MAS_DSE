# Name: Josh Wilson
# Email: jsw037@eng.ucsd.edu
# PID: A53228518

from pyspark import SparkContext
sc = SparkContext()

# Your program here
from pyspark.mllib.linalg import Vectors
from pyspark.mllib.regression import LabeledPoint

from string import split,strip

from pyspark.mllib.tree import GradientBoostedTrees, GradientBoostedTreesModel
from pyspark.mllib.tree import RandomForest, RandomForestModel

from pyspark.mllib.util import MLUtils


# ### Higgs data set
# * **URL:** http://archive.ics.uci.edu/ml/datasets/HIGGS#  
# * **Abstract:** This is a classification problem to distinguish between a signal process which produces Higgs bosons and a background process which does not.
# 
# **Data Set Information:**  
# The data has been produced using Monte Carlo simulations. The first 21 features (columns 2-22) are kinematic properties measured by the particle detectors in the accelerator. The last seven features are functions of the first 21 features; these are high-level features derived by physicists to help discriminate between the two classes. There is an interest in using deep learning methods to obviate the need for physicists to manually develop such features. Benchmark results using Bayesian Decision Trees from a standard physics package and 5-layer neural networks are presented in the original paper. The last 500,000 examples are used as a test set.

#define feature names
feature_text='lepton pT, lepton eta, lepton phi, missing energy magnitude, missing energy phi, jet 1 pt, jet 1 eta, jet 1 phi, jet 1 b-tag, jet 2 pt, jet 2 eta, jet 2 phi, jet 2 b-tag, jet 3 pt, jet 3 eta, jet 3 phi, jet 3 b-tag, jet 4 pt, jet 4 eta, jet 4 phi, jet 4 b-tag, m_jj, m_jjj, m_lv, m_jlv, m_bb, m_wbb, m_wwbb'
features=[strip(a) for a in split(feature_text,',')]

# Read the file into an RDD
# If doing this on a real cluster, you need the file to be available on all nodes, ideally in HDFS.
path='/HIGGS/HIGGS.csv'
inputRDD=sc.textFile(path)

# Transform the text RDD into an RDD of LabeledPoints
Data=inputRDD.map(lambda line: [float(strip(x)) for x in line.split(',')]).map(lambda line: LabeledPoint(line[:1][0],line[1:]))

# full dataset for cluster
Data1=Data.sample(False,0.1).cache()
(trainingData,testData)=Data1.randomSplit([0.7,0.3],seed=255)

# subset of dataset for local testing
#Data1=Data.sample(False,0.01).cache()
#(trainingData,testData)=Data1.randomSplit([0.7,0.3],seed=255)#.cache()


# gradient boosted tree model
errors={}
for depth in [10]:
    for lr in [0.2]:
        for numiter in [20]:
            model=GradientBoostedTrees.trainClassifier(trainingData, categoricalFeaturesInfo={}, 
                                                       numIterations=numiter, maxDepth=depth, 
                                                       learningRate=lr)
            errors[depth]={}
            dataSets={'train':trainingData,'test':testData}
            for name in dataSets.keys():  # Calculate errors on train and test sets
                data=dataSets[name]
                Predicted=model.predict(data.map(lambda x: x.features))
                LabelsAndPredictions=data.map(lambda LP: LP.label).zip(Predicted)
                Err = LabelsAndPredictions.filter(lambda (v,p):v != p).count()/float(data.count())
                errors[depth][name]=Err
            print depth,errors[depth]#,int(time()-start),'seconds'