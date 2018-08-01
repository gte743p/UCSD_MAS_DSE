import pandas as pd
import numpy as np
# from sklearn import cluster, datasets, mixture
# from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler
from itertools import cycle, islice
import time
import datetime
# import hdbscan
import joblib
import datetime
import os
from boto.utils import get_instance_metadata

from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sqlalchemy import create_engine

from sklearn.model_selection import PredefinedSplit, train_test_split, StratifiedKFold
import matplotlib.pyplot as plt

class Utility:

    
    """ Utility class to hold helper functions for data pre-processing and modeling.

    """

    def __init__(self, file_args):
        """ Constructor for Utility class.
        
        :param file_args: dict containing all arguments for the various helper functions
        :return: Utility instance.
        """

        self.file_args = file_args

        
    def get_modeling_data(self):
        """ Get modeling data from the database and split into train and test data sets.

        Splitting can be done either randomly or by date to allow for testing with a specific date range.

        :return: 2 data frames, 1 for the training data and 1 for the test data.
        """

        sql_modeling_data = 'SELECT * FROM modeling_data'
        modeling_data = pd.read_sql(sql_modeling_data, con=self.conn)
        
        # remove events and padres games if not included
        event_cols = [c for c in modeling_data.columns if c.startswith('event')]
#        if not self.file_args['add_events']:
#            modeling_data.drop(event_cols, axis=1, inplace=True)
#            print('removing events...')
#        if not self.file_args['add_padres']:
#            modeling_data.drop('padres_game', axis=1, inplace=True)
#            print('removing padres games...')
        
        # train test split
        train_data = modeling_data[modeling_data['train_test_{}'.format(self.file_args['train_test_method'])]=='train'].copy()
        test_data = modeling_data[modeling_data['train_test_{}'.format(self.file_args['train_test_method'])]=='test'].copy()
        train_data.drop(columns=[c for c in train_data.columns if c.startswith('train_test')], inplace=True)
        test_data.drop(columns=[c for c in test_data.columns if c.startswith('train_test')], inplace=True)
        
        # fix clustering columns
        train_data.rename(columns={'cluster_{}_{}'.format(self.file_args['cluster_method'],self.file_args['train_test_method']):'cluster'}, inplace=True)
        test_data.rename(columns={'cluster_{}_{}'.format(self.file_args['cluster_method'],self.file_args['train_test_method']):'cluster'}, inplace=True)
        train_data.drop(columns=[c for c in train_data.columns if c.startswith('cluster_')], inplace=True)
        test_data.drop(columns=[c for c in test_data.columns if c.startswith('cluster_')], inplace=True)    

        return train_data, test_data


    def unskew_data(self, data, neg_pos_ratio):
        """ Unskew a dataframe.

        Splits the data into positive and negative dataframes based on the leve_binary column, then performs a sample
        (with the seed from the args file for repeatability) from the negative dataframe, and finally concatenates the
        sampled negative dataframe to the positive dataframe.

        :param data: Pandas dataframe.
        :param neg_pos_ratio: Desired ratio of negative to positive data in results
        :return: dataframe of unskewed data.
        """
        # split into positive and negative
        pos_df = data[data['level_binary']>0]
        neg_df = data[data['level_binary']==0]

        # randomly sample negative rows
        pos_rows = pos_df.shape[0]
        neg_df_sampled = neg_df.sample(n = pos_rows*neg_pos_ratio, 
                                       random_state=self.file_args['seed'])

        # concatenate positives and sampled negatives
        unskewed_data = pd.concat([pos_df, neg_df_sampled], axis=0)
        return unskewed_data


    def get_neg_pos_ratio(self, data):
        """ Get the negative to positive traffic congestion data (level_binary column) of the given dataframe.

        :param data: dataframe containing traffic congestion data with a level_binary field indicating the presence of traffic.
        :return: Negative positive ration as a float.
        """

        pos_df = data['level_binary'].sum()
        neg_df = data.shape[0] - pos_df
        neg_pos_ratio = neg_df*1.0 / pos_df if pos_df > 0 else 99999
        return round(neg_pos_ratio,1)


    def create_week_cv_folds(self, data, num_weeks):
        """ Create cross validation folds by week.

        Can be used to create cross validation folds for 1 week periods

        :param data: Dataframs of traffic data.
        :param num_weeks: Number of weeks to hold out for cross validation.
        :return: Numpy array of data with -1 indicating training data.
        """

        # create array of -1 values to indicate training set
        week_folds = np.repeat(-1, len(data))

        # get last date of data - either last date of input data, or last date before test_date_start
        #last_date = data['date'].max()
        last_date = datetime.datetime.strptime(self.file_args['test_date_start'], '%m/%d/%Y').date() - pd.Timedelta(days=1)
        
        # set final num_weeks number of weeks to different validation folds
        for wk in range(num_weeks):
            wk_end = last_date - pd.Timedelta(days=wk*7)
            wk_start = wk_end - pd.Timedelta(days=7)
            val_indices = np.where((data['date'] > wk_start) & (data['date'] <= wk_end))
            week_folds[val_indices] = wk
        return week_folds


    def process_train_test(self, data, split_method=None):
        """ Perform train test split on the provided dataframe by the provided method.

        Splitting can be done either randomly or by date to allow for testing with a specific date range.
        Will unskew the training and or test data before returning if the flag has been set in the args file.

        :param data: Dataframe of traffic data
        :param split_method: how to split data (random or by date)
        :return: 2 data frames, 1 for the training data and 1 for the test data.
        """

        if split_method == None:
            split_method = self.file_args['train_test_method']
        if split_method == 'date':
            train_data = data[(data['date'] < datetime.datetime.strptime(self.file_args['test_date_start'], '%m/%d/%Y').date()) |
                              (data['date'] > datetime.datetime.strptime(self.file_args['test_date_end'], '%m/%d/%Y').date())]
            test_data = data[(data['date'] >= datetime.datetime.strptime(self.file_args['test_date_start'], '%m/%d/%Y').date()) &
                             (data['date'] <= datetime.datetime.strptime(self.file_args['test_date_end'], '%m/%d/%Y').date())]
        else:
            train_data, test_data = train_test_split(data, test_size=self.file_args['model_test_ratio'], 
                                                     random_state=self.file_args['seed'])
            
        print("train date range: "+str(min(train_data['date']))+" - "+str(max(train_data['date'])))
        print("test date range: "+str(min(test_data['date']))+" - "+str(max(test_data['date'])))
        
        # calculate negative to positive ratio in train and test data
        trn_ratio = self.get_neg_pos_ratio(train_data)
        tst_ratio = self.get_neg_pos_ratio(test_data)
        print('negative positive ratio in train data = {:01.1f}'.format(trn_ratio))
        print('negative positive ratio in test data = {:01.1f}'.format(tst_ratio))
        
        if (self.file_args['unskew_train'] and trn_ratio > self.file_args['unskew_ratio']):
            print('unskewing train data to negative positive ratio of {}...'.format(self.file_args['unskew_ratio']))
            train_data = self.unskew_data(train_data, self.file_args['unskew_ratio'])
        else:
            print('not unskewing train data...')
            
        if (self.file_args['unskew_test'] and tst_ratio > self.file_args['unskew_ratio']):
            print('unskewing test data to negative positive ratio of {}...'.format(self.file_args['unskew_ratio']))
            test_data = util.unskew_data(test_data, self.file_args['unskew_ratio'])
        else:
            print('not unskewing test data...')
        
        return train_data, test_data


    def get_validation_splits(self, data):
        """ Create cross validation folds of validation data either by date or randomly.

        :param data:Dataframe to split
        :return: Stratified folds of the validation split values.
        """

        if self.file_args['train_test_method'] == 'date':
            week_folds = self.create_week_cv_folds(data, self.file_args['num_cv_folds'])
            ps = PredefinedSplit(week_folds)
        if self.file_args['train_test_method'] == 'random':
            ps = StratifiedKFold(n_splits=self.file_args['num_cv_folds'], shuffle=False, random_state=self.file_args['seed'])
        return ps


    def add_best_models(self, val_dict):
        """ Add best model to provided results dictionary.

        :param val_dict: Dictionary to be updated.
        :return: None, val_dict is updated in place.
        """

        for stage in ['stage_1', 'stage_2']:
            best_models_dict = {}
            for clust in val_dict[stage]['cluster_counts'].keys():
                best_clust_score = 0
                for model in val_dict[stage].keys():
                    if str.startswith(model, 'model'):
                        clust_score = val_dict[stage][model][clust]
                        if clust_score > best_clust_score:
                            best_models_dict[clust] = model
                            best_clust_score = clust_score
            val_dict[stage]['best_models'] = best_models_dict


    def get_predefined_val_split(self, data):
        """ Get a predefined validation split for use in the Step 2 Evaluating Models notebook.
        
        Marks data as training or validation using a numpy array with -1 to indicate training data
        and 0 to indicate validation data.

        See this link for more details:
        https://stackoverflow.com/questions/43764999/python-machine-learning-perform-a-grid-search-on-custom-validation-set/43766334#43766334

        :param data: Dataframe to split.
        :return: Numpy array of data with -1 indicating training data.
        """

        # create array of -1 values to indicate training set
        val_fold = np.repeat(-1, len(data))

        # set validation set indices to 0
        if self.file_args['train_val_method'] == 'date':
            # get indices where date is within val_date range
            val_indices = np.where((data['date'] >= datetime.datetime.strptime(self.file_args['val_date_start'], '%m/%d/%Y').date()) &
                                   (data['date'] <= datetime.datetime.strptime(self.file_args['val_date_end'], '%m/%d/%Y').date()))

        if self.file_args['train_val_method'] == 'random':
            # get random sample of indices
            val_indices = np.random.choice(len(data), 
                                           size=int(round(len(data)*self.file_args['model_val_ratio'])),
                                           replace=False)
        
        val_fold[val_indices] = 0
        return val_fold


    def get_best_model(self, stage, cluster):
        """ Get the best model for the given cluster in the given modeling stage.

        Best model is determined by reading the val_results_dict.pkl file.

        :param stage: Stage of modeling: 1 (binary is traffic) or 2 (level of traffic assuming traffic in stage 1).
        :param cluster: Cluster number to find best model for.
        :return: best model object and model type description string.
        """

        bmf = os.path.join(self.file_args['save_dir'], 'val_results_dict.pkl')
        best_models = joblib.load(bmf)
        best_model_type = best_models['stage_' + str(stage)]['best_models'][cluster]
        # print('bmt', best_model_type)
        if best_model_type.find('cluster') > -1:
            model_filename = 'stage' + str(stage) + '_' + best_model_type + '_cluster_' + str(cluster) + '.pkl'
            model_filename = os.path.join(self.file_args['save_dir'], model_filename)
        else:
            model_filename = 'stage' + str(stage) + '_' + best_model_type + '.pkl'
            model_filename = os.path.join(self.file_args['save_dir'], model_filename)
        # print('bmfn', model_filename)
        best_model = joblib.load(model_filename)

        return best_model, best_model_type


    def isAWS(self):
        """ Determine if code is running on an AWS EC2 instance.

        :return: True if running on AWS EC2 instance.
        """

        m = get_instance_metadata(timeout=0.5, num_retries=3)
        if len(m.keys()) > 0:
            return True
        return False

    
    def metrics_plot_model(self, results_dict, stage='stage_1', score_metric='f1_score', sort=True, title_prefix=''):
        """ Create a plot showing modeling score for the provided metric from the results_dict.

        :param results_dict: Dictionary containing model results.
        :param stage: Stage of modeling: 1 (binary is traffic) or 2 (level of traffic assuming traffic in stage 1).
        :param score_metric: Meetric to plot on (f1_score is the default).
        :param sort: Should results be sorted (boolean).
        :return: None, a plot is shown in the calling notebook.
        """

        metrics = pd.DataFrame.from_dict(results_dict[stage])
        if 'best_models' in metrics.columns:
            metrics.drop(columns=['best_models'], inplace=True)

        # get cluster pct from counts
        clust_pct_arr = np.array(metrics['cluster_counts'] / metrics['cluster_counts'].sum())
        metrics.drop(columns=['cluster_counts'], inplace=True)

        # create row for 'all' score and append to df
        metrics_all_row = (metrics.transpose() * clust_pct_arr).sum(axis=1)
        metrics_all_df = pd.DataFrame(metrics_all_row).transpose()
        metrics_all_df.index = ['all']
        metrics = metrics.append(metrics_all_df).transpose().reset_index()

        if sort:
            metrics = metrics.sort_values(by='all', ascending=True)

        xlabels = metrics.loc[:,'index'].values
        c = range(len(xlabels))
        target = self.file_args['target_first_stage'] if stage=='stage_1' else self.file_args['target_second_stage']

        for col in metrics.columns:
            if col == 'all':
                plt.plot(c, metrics.loc[:,col], 'o--', label='{}'.format(col), color='black')
            elif col != 'index':
                plt.plot(c, metrics.loc[:,col], '.:', label='{}'.format(int(col)))

        plt.xticks(c, map(lambda s: s.replace('model_',''), xlabels), rotation=35)
        ax = plt.gca()
        ax.set_xticklabels(map(lambda s: s.replace('model_',''), xlabels), ha='right')
        plt.ylabel(score_metric)
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0., title='center')
        title_txt = '{} {} score by model'.format(title_prefix, target)
        plt.title(title_txt)
        plt.grid(axis='y', alpha=0.5)
        plt.savefig(os.path.join(self.file_args['save_dir'], title_txt+'.png'), bbox_inches='tight')
        plt.show();

        
    def metrics_plot_cluster(self, results_dict, stage='stage_1', score_metric='f1_score', sort_by_model='model_avg_baseline', title_prefix=''):
        """ Create a plot showing modeling score for the provided metric by cluster.

        :param results_dict: Dictionary containing model results.
        :param stage: Stage of modeling: 1 (binary is traffic) or 2 (level of traffic assuming traffic in stage 1).
        :param score_metric: Meetric to plot on (f1_score is the default).
        :param sort_by_model: Model to sort results on.
        :return: None, a plot is shown in the calling notebook.
        """

        metrics = pd.DataFrame.from_dict(results_dict[stage]).reset_index().rename(columns={'index':'cluster'})
        metrics = metrics.sort_values(by=sort_by_model, ascending=True)

        # add cluster_pct column
        metrics['cluster_pct'] = metrics['cluster_counts'] / metrics['cluster_counts'].sum()

        clusts = [clust for clust in metrics['cluster'].unique()]
        c = range(len(clusts))
        
        # see named color list @ https://matplotlib.org/2.0.0/examples/color/named_colors.html
        color_list = ['red','gray','blue','black','purple','green','darkred','royalblue','olive','yellowgreen',
                      'forestgreen','cadetblue','sienna','darksalmon']
        target = self.file_args['target_first_stage'] if stage=='stage_1' else self.file_args['target_second_stage']

        # plot overall and add labels
        model_cols = [mcol for mcol in metrics.columns if str.startswith(mcol, 'model')]
        for idx, col in enumerate(model_cols):
            overall_vals = np.repeat(sum(metrics[col] * metrics['cluster_pct']), len(c))
            label_txt = col.replace('model_','')
            plt.plot(c, overall_vals, label=label_txt, linestyle='-', color=color_list[idx], alpha=0.75)

        # add legend before adding second lines
        plt.legend()

        # plot clusters
        for idx, col in enumerate(model_cols):
            clust_vals = metrics.loc[:,col]
            plt.plot(c, clust_vals, linestyle=':', marker='+', color=color_list[idx], alpha=0.75)

        plt.grid(axis='y', alpha=0.5)
        plt.xlabel('cluster')
        plt.ylabel(score_metric)
        title_txt = '{} {} score by cluster'.format(title_prefix, target)
        plt.title(title_txt)
        plt.xticks(c, clusts)
        plt.savefig(os.path.join(self.file_args['save_dir'], title_txt+'.png'), bbox_inches='tight')
        plt.show();