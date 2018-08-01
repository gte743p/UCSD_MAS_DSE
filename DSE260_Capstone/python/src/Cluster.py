import pandas as pd
import numpy as np
from sklearn import cluster, datasets, mixture
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler
from itertools import cycle, islice
import hdbscan
import joblib
import datetime

from scipy.sparse import csr_matrix
from sklearn.decomposition import PCA
from sqlalchemy import create_engine
from sklearn import preprocessing


class Cluster:

    
    """Data and methods to cluster traffic data for modeling.

    This class is used to cluster traffic data by 1 or more methods and store the clusters
    in a table for use by other objects.


    Available clustering methods:
    MiniBatchKMeans:         Select all segments within a given radius of a provided point.

    AffinityPropagation:   Select all segments with a given bounding box.

    MeanShift:         Select a random sample of the provided percent from all segments.

    SpectralClustering:         Select all segments on a given street name.

    Ward:      Select all segments of a given road type.

    AgglomerativeClustering:         Select all segments with an Ignore flag of True.

    DBSCAN:    Select all segments such that the provided percent of positive traffic points are retained.

    Birch:    Select all segments such that the provided percent of positive traffic points are retained.

    HDBSCAN:    Select all segments such that the provided percent of positive traffic points are retained.

    KMeans:    Select all segments such that the provided percent of positive traffic points are retained.

    This class will be used in the Pipeline notebook for exploration purposes and in the Production
    python code used to perform the actual clustering and modeling of traffic data.

    """

    def __init__(self, conn, args, data, split_type, num_clusters):
        """Constructor for Cluster object.

        :param conn: database connection object.
        :param args: dict of arguments read from the arguments file.
        :param data: data to cluster.
        :param split_type: Split train test data randomly or by date to allow testing by specific date ranges.
        :param num_clusters: Number of clusters to create.
        :return: Cluster instance.
        """

        self.conn = conn
        self.args = args
        self.data = data
        self.split_type = split_type

        self.pca_model = None
        self.cluster_model = None
        self.algorithm = args['cluster_algorithm']

        # http://scikit-learn.org/stable/auto_examples/cluster/plot_cluster_comparison.html
        hdbsc = hdbscan.HDBSCAN(min_cluster_size=10)
        affinity_propagation = cluster.AffinityPropagation()
        ms = cluster.MeanShift(bin_seeding=True)
        spectral = cluster.SpectralClustering(n_clusters=num_clusters, 
                                              eigen_solver='arpack',
                                              affinity="nearest_neighbors", 
                                              random_state=self.args['seed'])
        ward = cluster.AgglomerativeClustering(n_clusters=num_clusters, 
                                               linkage='ward')
        birch = cluster.Birch(n_clusters=num_clusters)
        two_means = cluster.MiniBatchKMeans(n_clusters=num_clusters,
                                            random_state=self.args['seed'])
        average_linkage = cluster.AgglomerativeClustering(linkage="average", 
                                                          n_clusters=num_clusters)
        hdbsc = hdbscan.HDBSCAN(min_cluster_size=10)
        kmeans = cluster.KMeans(n_clusters=num_clusters, random_state=self.args['seed'])
        dbscan = cluster.DBSCAN()
        
        self.clustering_algorithms = {
            'MiniBatchKMeans': two_means,
            'AffinityPropagation': affinity_propagation,
            'MeanShift': ms,
            'SpectralClustering': spectral,
            'Ward': ward,
            'AgglomerativeClustering': average_linkage,
            'DBSCAN': dbscan,
            'Birch': birch,
            'HDBSCAN': hdbsc,
            'KMeans': kmeans
        } 

    def scale_matrix(self, matrix_df):
        """ Standardize matrix feature columns using sklearn.preprocessing.scale.

        :param matrix_df: Data frame of all segment and time combinations and feature columns.
        :return: Data frame containing only feature columns with scaled values.
        """

        print('scaling features...')

        originalkeys = matrix_df[['segment_id','date','time']].reset_index()
        originalkeys['index'] = originalkeys.index

        columns = list(matrix_df)
        columns.remove('segment_id')
        columns.remove('date')
        columns.remove('time')
        data_to_scale = matrix_df[columns]
        matrix_df_scaled_tmp = pd.DataFrame(preprocessing.scale(data_to_scale), columns = columns).reset_index()
        matrix_df_scaled_tmp['index']=matrix_df_scaled_tmp.index

        matrix_df_scaled_labels_tmp = pd.merge(matrix_df_scaled_tmp, originalkeys, on=['index'])
        matrix_df_scaled = matrix_df_scaled_tmp.drop(columns=['index'])
        matrix_df_scaled_withlabels = matrix_df_scaled_labels_tmp.drop(columns=['index'])
        
        return matrix_df_scaled_withlabels
    
    def run_PCA(self, sparse_matrix):
        """Perform PCA on the given sparse matrix.

        Perform PCA on the given sparse matrix and dump the PCA object to a pickle file. Sparse matrix feature array
        for each segment contains the cluster variable average over a time array of one week.

        :param sparse_matrix: spare matrix as created by self.create_sparse_matrix
        :return: The transformed data to cluster and the PCA model.
        """

        pca_explained = np.cumsum(PCA().fit(sparse_matrix).explained_variance_ratio_)
        pca_explainedby = np.where(pca_explained>=0.9)[0][0]
        pca = PCA(n_components=pca_explainedby)
        pca.fit(sparse_matrix)
        
        today = datetime.date.today()
        filename = 'sparse_pca_model.pkl'
        joblib.dump(pca, filename)
        
        return pca.transform(sparse_matrix), pca 
        
    def run_PCA_long(self, sparse_matrix):
        """Perform PCA on the given sparse long format matrix.

        Perform PCA on the given long format sparse matrix and dump the PCA object to a pickle file. The long format
        sparse matrix feature array for each segment contains cluster variable over time array of non-agreggated
        timespan of the dataset.

        :param sparse_matrix: spare matrix as created by self.create_sparse_matrix_long
        :return: The transformed data to cluster and the PCA model.
        """

        pca_explained = np.cumsum(PCA().fit(sparse_matrix).explained_variance_ratio_)
        pca_explainedby = np.where(pca_explained>=0.9)[0][0]
        pca = PCA(n_components=pca_explainedby)
        pca.fit(sparse_matrix)
        
        today = datetime.date.today()
        filename = 'sparse_long_pca_model.pkl'
        joblib.dump(pca, filename)
        
        return pca.transform(sparse_matrix), pca                 
        
    def create_sparse_matrix(self, matrix_df):
        """Create sparse matrix for use in clustering the data.

        In addition to creating and returning the sparse matrix, this function also writes the sparse matrix
        to the database for use in assigning clusters to new data at a later time. it creates database tables
        clust_sparse_avebysegment_[split_type] and clust_sparse_avebyrt_[split_type] for use in clustering the data.
        Sparse matrix feature array for each segment contains the cluster variable average over a time array of one week.

        :param matrix_df: Pandas data frame containing all relevant segments and time buckets.
        :return: tuple of 2 data frames. 1. Unique segments 2. The sparse matrix.
        """

        print('creating sparse matrix...')
        sparse_seg_tmp_df = matrix_df.groupby(['segment_id','day_of_week','time_idx'])[self.args['cluster_variable']].mean().reset_index()
        sparse_rt_tmp_df = matrix_df.groupby(['road_type','day_of_week','time_idx'])[self.args['cluster_variable']].mean().reset_index()
        time_seg_df = sparse_seg_tmp_df.groupby(['day_of_week','time_idx'])[self.args['cluster_variable']].mean().reset_index()
        time_rt_df = sparse_rt_tmp_df.groupby(['day_of_week','time_idx'])[self.args['cluster_variable']].mean().reset_index()
        #time_seg_df['time_id'] = time_seg_df.index
        #time_rt_df['time_id'] = time_rt_df.index
        times = list(range(24*60/self.args['time_resolution']))
        full_time_idx = pd.DataFrame([i * 30 for i in times],columns = ['time_idx'])
        full_time_idx['key'] = 1
        full_day_of_week = pd.DataFrame(list(range(7)), columns = ['day_of_week'])
        full_day_of_week['key'] = 1
        full_times = pd.merge(full_time_idx, full_day_of_week, on='key')
        full_times['time_id'] = full_times.index
        time_seg_df = pd.merge(time_seg_df, full_times[['time_idx','day_of_week','time_id']], on=['time_idx','day_of_week'])
        time_rt_df = pd.merge(time_rt_df, full_times[['time_idx','day_of_week','time_id']], on=['time_idx','day_of_week'])
        
        matrix_seg_keys_df = pd.merge(sparse_seg_tmp_df, time_seg_df[['time_id','day_of_week','time_idx']], how='left', on=['day_of_week','time_idx'])
        matrix_rt_keys_df = pd.merge(sparse_rt_tmp_df, time_rt_df[['time_id','day_of_week','time_idx']], how='left', on=['day_of_week','time_idx'])

        time_seg_array = np.array(matrix_seg_keys_df['time_id'])
        time_rt_array = np.array(matrix_rt_keys_df['time_id'])
        segment_array = np.array(matrix_seg_keys_df['segment_id'])
        rt_array = np.array(matrix_rt_keys_df['road_type'])

        uniquesegments = np.array(list(set(segment_array)))
        uniquerts = np.array(list(set(rt_array)))
        keyuniquesegments = np.array(range(len(uniquesegments)))
        keyuniquerts = np.array(range(len(uniquerts)))
        uniquesegments_df = pd.DataFrame({'segmentskey':keyuniquesegments, 'segment_id':uniquesegments})
        uniquerts_df = pd.DataFrame({'roadtypekey':keyuniquerts, 'road_type':uniquerts})

        segments_df = pd.DataFrame(segment_array, columns = ['segment_id'])
        rt_df = pd.DataFrame(rt_array, columns = ['road_type'])
        segments_keys_df = pd.merge(segments_df, uniquesegments_df, how='left', on=['segment_id'])
        rt_keys_df = pd.merge(rt_df, uniquerts_df, how='left', on=['road_type'])
        segmentkeys = np.array(segments_keys_df['segmentskey'])
        rtkeys = np.array(rt_keys_df['road_type'])

        level_array_seg = np.array(matrix_seg_keys_df['level_max'])
        sparse_matrix_s = csr_matrix((level_array_seg, (segmentkeys,time_seg_array))).toarray()
        sparse_matrix_seg = preprocessing.scale(sparse_matrix_s)
        level_array_rt = np.array(matrix_rt_keys_df['level_max'])
        sparse_matrix_r = csr_matrix((level_array_rt, (rtkeys,time_rt_array))).toarray()
        sparse_matrix_rt = preprocessing.scale(sparse_matrix_r)
        
        if self.args['perform_pca']:
            sparse_matrix_seg, self.pca_model = self.run_PCA(sparse_matrix_seg)
            sparse_matrix_rt, self.pca_model = self.run_PCA(sparse_matrix_rt)
        else:
            sparse_matrix_seg = sparse_matrix_seg
            sparse_matrix_rt = sparse_matrix_rt
        
        sparse_matrix_withsegkey = pd.DataFrame(sparse_matrix_seg)
        sparse_matrix_withrtkey = pd.DataFrame(sparse_matrix_rt)
        sparse_matrix_withsegkey['segmentskey'] = sparse_matrix_withsegkey.index
        sparse_matrix_withseg = pd.merge(uniquesegments_df, sparse_matrix_withsegkey,  on=['segmentskey'])
        sparse_matrix_withrtkey['roadtypekey'] = sparse_matrix_withrtkey.index
        sparse_matrix_withrt = pd.merge(uniquerts_df, sparse_matrix_withrtkey,  on=['roadtypekey'])
        
        # write sparse_matrix to database as 'clustering' table
        print('writing sparse matrix to db...')
        sqlalchemy_conn_str = open('../conf/sqlalchemy_conn_str.txt', 'r').read()
        engine = create_engine(sqlalchemy_conn_str)
        if self.split_type == 'random':
            sparse_matrix_withseg.to_sql(name='clust_sparse_avebysegment_random', con=engine, if_exists='replace')
            sparse_matrix_withrt.to_sql(name='clust_sparse_avebyrt_random', con=engine, if_exists='replace')
        elif self.split_type == 'date':
            sparse_matrix_withseg.to_sql(name='clust_sparse_avebysegment_date', con=engine, if_exists='replace')
            sparse_matrix_withrt.to_sql(name='clust_sparse_avebyrt_date', con=engine, if_exists='replace')
        
        print('returning train sparse matrix...')
        return (uniquesegments_df, sparse_matrix_seg)

    def create_sparse_matrix_long(self, matrix_df):
        """Create sparse matrix in long format for use in clustering the data.

        In addition to creating and returning the long format sparse matrix, this function also writes the sparse matrix
        to the database for use in assigning clusters to new data at a later time. It create database tables
        clust_sparse_long_avebysegment_[split_type] and clust_sparse_long_avebyrt_[split_type] for use in clustering
        the data. Sparse matrix feature array for each segment contains cluster variable over a time array of
        non-aggregated timespan of the dataset.

        :param matrix_df: Pandas data frame containing all relevant segments and time buckets.
        :return: tuple of 2 data frames. 1. Unique segments 2. The sparse matrix.
        """

        time_df_tmp = matrix_df.groupby(['date_idx','time_idx']).count().reset_index()
        time_df = time_df_tmp[['date_idx','time_idx']]
        time_df['time_id'] = time_df.index.copy()
        matrix_df_tid = pd.merge(matrix_df, time_df, how='left', on=['date_idx','time_idx'])

        time_array = np.array(matrix_df_tid['time_id'])
        segment_array = np.array(matrix_df_tid['segment_id'])

        uniquesegments = np.array(list(set(segment_array)))
        keyuniquesegments = np.array(range(len(uniquesegments)))
        uniquesegments_df = pd.DataFrame({'segmentskey':keyuniquesegments, 'segment_id':uniquesegments})

        segments_df = pd.DataFrame(segment_array, columns = ['segment_id'])
        segments_keys_df = pd.merge(segments_df, uniquesegments_df, how='left', on=['segment_id'])
        segmentkeys = np.array(segments_keys_df['segmentskey'])

        level_array = np.array(matrix_df_tid[self.args['cluster_variable']])
        sparse_matrix = csr_matrix((level_array, (segmentkeys,time_array))).toarray()
        sparse_matrix = preprocessing.scale(sparse_matrix)
        
        if self.args['perform_pca']:
            data_to_cluster, self.pca_model = self.run_PCA_long(sparse_matrix)
        else:
            data_to_cluster = sparse_matrix

        sparse_matrix_withsegkey = pd.DataFrame(data_to_cluster)
        sparse_matrix_withsegkey['segmentskey'] = sparse_matrix_withsegkey.index
        sparse_matrix_withseg = pd.merge(uniquesegments_df, sparse_matrix_withsegkey,  on=['segmentskey'])
        
        print('writing sparse matrix_long to db...')
        sqlalchemy_conn_str = open('../conf/sqlalchemy_conn_str.txt', 'r').read()
        engine = create_engine(sqlalchemy_conn_str)
        if self.split_type == 'random':
            sparse_matrix_withseg.to_sql(name='clust_sparse_long_avebysegment_random', con=engine, if_exists='replace')
        elif self.split_type == 'date':
            sparse_matrix_withseg.to_sql(name='clust_sparse_long_avebysegment_date', con=engine, if_exists='replace')
        
        print('returning train sparse_long matrix...')
        return (uniquesegments_df, data_to_cluster)
    
        
    def create_nonsparse_matrix(self, matrix_df):
        """Create non-sparse matrix for use in clustering the data.

        In addition to creating and returning the non-sparse matrix, this function also writes the non-sparse matrix
        to the database for use in assigning clusters to new data at a later time. It creates database tables
        clust_nonsparse_avebysegment_[split_type] and clust_nonsparse_avebyrt_[split_type] for use in clustering the
        data. Nonsparse matrix feature array for each segment-time record contains all features in matrix_df.

        :param matrix_df: Pandas data frame containing all relevant segments and time buckets.
        :return: tuple of 2 data frames. 1. Unique segments 2. The non-sparse matrix.
        """

        print('creating nonsparse matrix...')
        clustering_df_tmp = matrix_df[['date','time','date_idx', 'time_idx', 'day_of_week', 'segment_id', 'road_type', 'lat1', 'lat2', 'lon1', 'lon2', 'level_min', 'level_max', 'level_mean', 'level_count', 'level_binary']]
        seg_averages = clustering_df_tmp.groupby(['segment_id', 'day_of_week', 'time_idx'])[['level_min', 'level_max', 'level_mean', 'level_count', 'level_binary']].mean().reset_index()
        rt_averages = clustering_df_tmp.groupby(['road_type', 'day_of_week', 'time_idx'])[['level_min', 'level_max', 'level_mean', 'level_count', 'level_binary']].mean().reset_index()
        
        # write nonsparse_matrix_db to database as 'clustering' table
        print('writing nonsparse matrix to db...')
        sqlalchemy_conn_str = open('../conf/sqlalchemy_conn_str.txt', 'r').read()
        engine = create_engine(sqlalchemy_conn_str)
        if self.split_type == 'random':
            seg_averages.to_sql(name='clust_nonsparse_avebysegment_random', con=engine, if_exists='replace')
            rt_averages.to_sql(name='clust_nonsparse_avebyrt_random', con=engine, if_exists='replace')
        elif self.split_type == 'date':
            seg_averages.to_sql(name='clust_nonsparse_avebysegment_date', con=engine, if_exists='replace')
            rt_averages.to_sql(name='clust_nonsparse_avebyrt_date', con=engine, if_exists='replace')
        
        print('returning train nonsparse matrix...')
        train_averages = clustering_df_tmp.groupby(['segment_id', 'day_of_week', 'time_idx'])[['level_min', 'level_max', 'level_mean', 'level_count','level_binary']].mean().reset_index()
        train_averages.columns = ['segment_id', 'day_of_week', 'time_idx', 'ave_level_min', 'ave_level_max', 'ave_level_mean', 'ave_level_count', 'ave_level_binary']
        nonsparse_matrix = pd.merge(clustering_df_tmp, train_averages, how='left', on=['segment_id', 'day_of_week', 'time_idx'])
        segtimes_df = nonsparse_matrix[['segment_id', 'date', 'time']]
        nonsparse_matrix_final = nonsparse_matrix.drop(columns=['segment_id', 'date','time', 'level_min', 'level_max', 'level_mean', 'level_count', 'level_binary'])
        
        return (segtimes_df, nonsparse_matrix_final)      
        
    
    def train_clustermodel_sparse(self):
        """ Create clustering model from the sparse matrix dataframe.

        Creates the clustering model with the current clustering algorithm from either the raw or PCA transformed
        data as created by self.create_sparse_matrix. It also saves the model in a pickle file for future use.

        :return: Clustering model and a dataframe of the sparse matrix with each row's assigned cluster.
        """

        print('Clustering using: ' + self.algorithm)
        uniquesegments_df, sparse_matrix = self.create_sparse_matrix(self.data)

        clusterer = self.clustering_algorithms[self.algorithm]
        self.clustering_model = clusterer.fit(sparse_matrix)
        
        clusters_df = pd.DataFrame(self.clustering_model.labels_, columns = ['cluster_sparse'])
        clusters_df['segmentskey'] = clusters_df.index
        clusters_df = clusters_df.reset_index(drop=True)
        self.clusters_df_final = pd.merge(uniquesegments_df, clusters_df,  on=['segmentskey'])
        self.clusters_df_final['cluster_sparse'].value_counts()
        
        today = datetime.date.today()
        filename = self.algorithm + '_sparse_cluster_model_' + today.strftime('%Y%m%d') + '.pkl'
        joblib.dump(self.clustering_model, filename)
        
        print('Stored ' + filename)
        
        return self.clustering_model, self.clusters_df_final[['segment_id','cluster_sparse']]
    
    
    def train_clustermodel_sparse_long(self):
        """ Create clustering model from the long format sparse matrix dataframe.

        This function creates the clustering model with the current clustering algorithm
        from either the raw or PCA transformed data as created by self.create_sparse_matrix_long.
        It also saves the model in a pickle file for future use.

        :return: Clustering model and a dataframe of the long format sparse matrix with each row's assigned cluster.
        """

        print('Clustering using: ' + self.algorithm)
        uniquesegments_df, sparse_matrix = self.create_sparse_matrix_long(self.data)

        clusterer = self.clustering_algorithms[self.algorithm]
        self.clustering_model = clusterer.fit(sparse_matrix)
        
        clusters_df = pd.DataFrame(self.clustering_model.labels_, columns = ['cluster_sparse_long'])
        clusters_df['segmentskey'] = clusters_df.index
        clusters_df = clusters_df.reset_index(drop=True)
        self.clusters_df_final = pd.merge(uniquesegments_df, clusters_df,  on=['segmentskey'])
        self.clusters_df_final['cluster_sparse_long'].value_counts()
        
        today = datetime.date.today()
        filename = self.algorithm + '_sparse_long_cluster_model_' + today.strftime('%Y%m%d') + '.pkl'
        joblib.dump(self.clustering_model, filename)
        
        print('Stored ' + filename)
        
        return self.clustering_model, self.clusters_df_final[['segment_id','cluster_sparse_long']]
        
    
    def train_clustermodel_nonsparse(self): 
        """ Create clustering model from the non-sparse matrix dataframe.

        This function creates the clustering model with the current clustering algorithm
        from either the raw or PCA transformed data as created by self.create_nonsparse_matrix.
        It also saves the model in a pickle file for future use.

        :return: Clustering model and a dataframe of the non-sparse matrix with each row's assigned cluster.
        """
               
        segtimes_df, nonsparse_matrix =  self.create_nonsparse_matrix(self.data)
        segtimes_df['index']=segtimes_df.index
        nonsparse_matrix['index']=nonsparse_matrix.index
        data_to_scale = pd.merge(segtimes_df, nonsparse_matrix, on=['index'])
        data_scaled = self.scale_matrix(data_to_scale)
        data_to_cluster = data_scaled.drop(columns = ['segment_id','level_0','date','time'])
        
        print('Clustering using nonsparse segment/time matrix and: ' + self.algorithm)
        clusterer = self.clustering_algorithms[self.algorithm]
        self.clustering_model = clusterer.fit(data_to_cluster)
        
        clusters_df = pd.DataFrame(self.clustering_model.labels_, columns = ['cluster_nonsparse'])
        clusters_df['segtimekey'] = clusters_df.index
        segtimes_df['segtimekey'] = segtimes_df.index
        clusters_df = clusters_df.reset_index(drop=True)
        self.clusters_df_final = pd.merge(segtimes_df, clusters_df,  on=['segtimekey'])
        self.clusters_df_final['cluster_nonsparse'].value_counts()
        
        today = datetime.date.today()
        filename = self.algorithm + '_nonsparse_cluster_model_' + today.strftime('%Y%m%d') + '.pkl'
        joblib.dump(self.clustering_model, filename)
        
        print('Stored ' + filename)
        
        return self.clustering_model, self.clusters_df_final[['segment_id','date','time','cluster_nonsparse']]    
                                         
    def test_assign_clusters_sparse(self, new_data, filename):
        """ Assign clusters to a new sparse matrix dataframe.

        This function assigns clusters to the provided sparse matrix using the current clustering model
        and returns the sparse matrix with the assigned clusters.
        It reads the feature array for segments from database table clust_sparse_avebysegment_[split_type] (segment averages)
        if the segment exists or from clust_sparse_avebyrt_[split_type] (road type averages) if segment is new.
        It then loads the cluster model from the pickle file amd assigns clusters to the provided data.

        :param new_data: New data in sparse matrix format to assign clusters to.
        :param filename: Filename of saved clustiern model pickle file.

        :return: dataframe of the sparse matrix with each row's assigned cluster.
        """

        sqlalchemy_conn_str = open('../conf/sqlalchemy_conn_str.txt', 'r').read()
        engine = create_engine(sqlalchemy_conn_str)
        
        print('creating test sparse matrix...')
        if self.split_type == 'random':
            averages_seg = pd.read_sql('SELECT * FROM clust_sparse_avebysegment_random',con=engine)
            averages_rt = pd.read_sql('SELECT * FROM clust_sparse_avebyrt_random',con=engine)
        if self.split_type == 'date':
            averages_seg = pd.read_sql('SELECT * FROM clust_sparse_avebysegment_date',con=engine)
            averages_rt = pd.read_sql('SELECT * FROM clust_sparse_avebyrt_date',con=engine)

        averages_seg['exists'] = 1
        test_data_exists = pd.merge(new_data, averages_seg[['segment_id', 'exists']], on=['segment_id'])
        test_exists = test_data_exists[test_data_exists['exists']==1]
        test_notexists = test_data_exists[test_data_exists['exists']!=1]  
        
        test_matrix_exists = pd.merge(test_exists[['segment_id', 'road_type']], averages_seg, how='left', on=['segment_id'])
        test_matrix_notexists = pd.merge(test_notexists[['segment_id', 'road_type']], averages_rt, how='left', on=['road_type'])
        test_matrix = pd.concat([test_matrix_exists, test_matrix_notexists])
        test_matrix = test_matrix.fillna(0)        
        
        test_sparse_matrix = test_matrix.drop(columns = ['segment_id', 'road_type', 'exists', 'index', 'roadtypekey', 'segmentskey'])
        num = list(range(len(list(averages_seg))-4))
        columns = [str(item) for item in num]
        test_sparse_matrix = test_sparse_matrix[columns] 
        
        print('clustering new data...')
        cluster_model = joblib.load(filename)
        cluster_predictions = cluster_model.predict(test_sparse_matrix)
        
        clusterdf = pd.DataFrame(cluster_predictions,columns = ['cluster_sparse'])
        clusterdf['index'] = clusterdf.index
        segmentdf = test_matrix['segment_id'].to_frame()
        segmentdf['index'] = segmentdf.index
        test_cluster_df_sparse = pd.merge(clusterdf, segmentdf,  on=['index'])
        test_cluster_df_sparse = test_cluster_df_sparse[['segment_id','cluster_sparse']].groupby(['segment_id','cluster_sparse']).count()
        
        return test_cluster_df_sparse.reset_index()
    
    def test_assign_clusters_sparse_long(self, new_data, filename):
        """ Assign clusters to a new long format sparse matrix dataframe.

        This function assigns clusters to the provided long format sparse matrix using the current clustering model
        and returns the long format sparse matrix with the assigned clusters.
        It reads the feature array for segments from database table clust_sparse_long_avebysegment_[split_type]
        (segment averages) if the segment exists or from clust_sparse_long_avebyrt_[split_type] (road type averages)
        if segment is new. It then loads the cluster model from the pickle file amd assigns clusters to the provided data.

        :param new_data: New data in long format sparse matrix format to assign clusters to.
        :param filename: Filename of saved clustiern model pickle file.

        :return: dataframe of the long format sparse matrix with each row's assigned cluster.
        """

        sqlalchemy_conn_str = open('../conf/sqlalchemy_conn_str.txt', 'r').read()
        engine = create_engine(sqlalchemy_conn_str)
        
        print('creating test sparse matrix...')
        if self.split_type == 'random':
            averages_seg = pd.read_sql('SELECT * FROM clust_sparse_long_avebysegment_random',con=engine)
        if self.split_type == 'date':
            averages_seg = pd.read_sql('SELECT * FROM clust_sparse_long_avebysegment_date',con=engine)
      
        test_matrix = pd.merge(new_data['segment_id'].to_frame(), averages_seg, how='inner', on=['segment_id'])
        test_sparse_matrix = test_matrix.drop(columns = ['segment_id','segmentskey','index'])
        
        print('clustering new data...')
        cluster_model = joblib.load(filename)
        cluster_predictions = cluster_model.predict(test_sparse_matrix)
        
        clusterdf = pd.DataFrame(cluster_predictions,columns = ['cluster_sparse_long'])
        clusterdf['index'] = clusterdf.index
        segmentdf = test_matrix['segment_id'].to_frame()
        segmentdf['index'] = segmentdf.index
        test_cluster_df_sparse = pd.merge(clusterdf, segmentdf,  on=['index'])
        test_cluster_df_sparse = test_cluster_df_sparse[['segment_id', 'cluster_sparse_long']].groupby(['segment_id', 'cluster_sparse_long']).count()
        
        return test_cluster_df_sparse.reset_index()

    def test_assign_clusters_nonsparse(self, new_data, filename):
        """ Assign clusters to a new non-sparse matrix dataframe.

        This function assigns clusters to the provided non-sparse matrix using the current clustering model
        and returns the non-sparse matrix with the assigned clusters.
        It reads the feature array for segments from database table clust_nonsparse_avebysegment_[split_type] (segment averages)
        if the segment exists or from clust_nonsparse_avebyrt_[split_type] (road type averages) if segment is new.
        It then loads the cluster model from the pickle file amd assigns clusters to the provided data.

        :param new_data: New data in non-sparse matrix format to assign clusters to.
        :param filename: Filename of saved clustiern model pickle file.

        :return: dataframe of the non-sparse matrix with each row's assigned cluster.
        """

        sqlalchemy_conn_str = open('../conf/sqlalchemy_conn_str.txt', 'r').read()
        engine = create_engine(sqlalchemy_conn_str)
        if self.split_type == 'random':
            averages_seg = pd.read_sql('SELECT * FROM clust_nonsparse_avebysegment_random',con=engine)
            averages_rt = pd.read_sql('SELECT * FROM clust_nonsparse_avebyrt_random',con=engine)
        elif self.split_type == 'date':
            averages_seg = pd.read_sql('SELECT * FROM clust_nonsparse_avebysegment_date',con=engine)
            averages_rt = pd.read_sql('SELECT * FROM clust_nonsparse_avebyrt_date',con=engine)
        
        averages_seg['exists'] = 1
        test_data_exists = pd.merge(new_data, averages_seg[['segment_id', 'day_of_week', 'time_idx', 'exists']], on=['segment_id', 'day_of_week', 'time_idx'])
        test_exists = test_data_exists[test_data_exists['exists']==1]
        test_notexists = test_data_exists[test_data_exists['exists']!=1]
        
        test_exists_tmp = test_exists[['date','time','date_idx', 'time_idx', 'day_of_week', 'segment_id', 'road_type', 'lat1', 'lat2', 'lon1', 'lon2']]
        test_notexists_tmp = test_notexists[['date','time','date_idx', 'time_idx', 'day_of_week', 'segment_id', 'road_type', 'lat1', 'lat2', 'lon1', 'lon2']]
        test_matrix_exists = pd.merge(test_exists_tmp, averages_seg, how='left', on=['segment_id', 'day_of_week', 'time_idx'])
        test_matrix_notexists = pd.merge(test_notexists_tmp, averages_rt, how='left', on=['road_type', 'day_of_week', 'time_idx'])
        test_matrix = pd.concat([test_matrix_exists, test_matrix_notexists])
        test_matrix = test_matrix.fillna(0)
        
        test_nonsparse_matrix = test_matrix[['segment_id','date','time','date_idx', 'time_idx', 'day_of_week', 'road_type', 'lat1', 'lat2', 'lon1', 'lon2', 'level_binary', 'level_min', 'level_max', 'level_mean', 'level_count']]
        test_nonsparse_matrix = self.scale_matrix(test_nonsparse_matrix)

        print('clustering new data...')
        cluster_model = joblib.load(filename)
        cluster_predictions = cluster_model.predict(test_nonsparse_matrix.drop(columns = ['segment_id','date','time']))
        
        clusterdf = pd.DataFrame(cluster_predictions,columns = ['cluster_nonsparse']).reset_index()
        keydf = test_matrix[['segment_id','date','time']].reset_index()
        test_cluster_df_sparse = pd.merge(clusterdf, keydf,  on=['index'])
        
        return test_cluster_df_sparse[['segment_id','date','time','cluster_nonsparse']]    