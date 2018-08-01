import boto3
# from boto.utils import get_instance_metadata

class AWS:

    """ Methods to connect to AWS EC2 and read and write files from S3.
    """

    def __init__(self, bucket_name, data_dir):
        """Constructor for AWS object.

        :param bucket_name: S3 bucket name.
        :param data_dir: local directory containing saved files.
        :return: AWS instance.
        """

        self.s3 = boto3.resource('s3')
        self.bucket_name = bucket_name
        self.data_dir = data_dir  
        self.db_server = '18.232.11.160'
        self.db_port = '5432'
        self.db_name = 'waze_schema'
        self.db_user = 'dsewaze'
        self.db_pwd = '123456'
    

    def save_file(self, filename, args):
        """ Save file to S3 bucket.

        :param filename: Filename to save to S3.
        :param args: dict of data to write to S3.
        :return: True
        """

        obj = self.data_dir + '/' + filename
        s3.Bucket(self.bucket_name).put_object(Key=obj, Body=pickle.dumps(args))
        
                                               
    def read_file(self, filename):
        """ Read file from S3 bucket.

        :param filename: Filename to read from S3 bucket.
        :return: File read from S3 bucket.
        """

        path = self.data_dir + '/' + filename
        obj = self.s3.Object(self.bucket_name, path)
        test_data = pickle.loads(obj.get()['Body'].read())



