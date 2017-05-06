""" Code from cs231n course """
import six.moves.cPickle as pickle
import numpy as np
import os, sys, random
from imread import imread
import cv2
from sklearn.datasets import fetch_mldata
from scipy.misc import imread

def load_CIFAR_batch(filename):
    """ load single batch of cifar """
    with open(filename, 'rb') as f:
        if sys.version_info > (3, 0):
            datadict = pickle.load(f, encoding='latin1')
        else:
            datadict = pickle.load(f)
        X = datadict['data']
        Y = datadict['labels']
        X = X.reshape(10000, 3, 32, 32).transpose(0, 2, 3, 1).astype("float")
        Y = np.array(Y)
        return X, Y


def load_CIFAR10(ROOT):
    """ load all of cifar """
    xs = []
    ys = []
    for b in range(1, 6):
        f = os.path.join(ROOT, 'data_batch_%d' % (b,))
        X, Y = load_CIFAR_batch(f)
        xs.append(X)
        ys.append(Y)
    Xtr = np.concatenate(xs)
    Ytr = np.concatenate(ys)
    del X, Y
    Xte, Yte = load_CIFAR_batch(os.path.join(ROOT, 'test_batch'))
    return Xtr, Ytr, Xte, Yte


def get_CIFAR10_data(data_dir,
                     num_training=49000,
                     num_validation=1000,
                     num_test=1000):
    """
    Load the CIFAR-10 dataset from disk and perform preprocessing to prepare
    it for classifiers. These are the same steps as we used for the SVM, but
    condensed to a single function.
    """
    # Load the raw CIFAR-10 data
    X_train, y_train, X_test, y_test = load_CIFAR10(data_dir)

    # Subsample the data
    mask = range(num_training, num_training + num_validation)
    X_val = X_train[mask]
    y_val = y_train[mask]
    mask = range(num_training)
    X_train = X_train[mask]
    y_train = y_train[mask]
    mask = range(num_test)
    X_test = X_test[mask]
    y_test = y_test[mask]

    # Normalize the data: subtract the mean image
    mean_image = np.mean(X_train, axis=0)
    X_train -= mean_image
    X_val -= mean_image
    X_test -= mean_image

    # Transpose so that channels come first
    X_train = X_train.transpose(0, 3, 1, 2).copy()
    X_val = X_val.transpose(0, 3, 1, 2).copy()
    X_test = X_test.transpose(0, 3, 1, 2).copy()

    # Package data into a dictionary
    return {
        'X_train': X_train,
        'y_train': y_train,
        'X_val': X_val,
        'y_val': y_val,
        'X_test': X_test,
        'y_test': y_test,
    }


def load_tiny_imagenet(path, dtype=np.float32):
    """Load TinyImageNet. Each of TinyImageNet-100-A, TinyImageNet-100-B, and
    TinyImageNet-200 have the same directory structure, so this can be used
    to load any of them.

    Inputs:
        - path: String giving path to the directory to load.
        - dtype: numpy datatype used to load the data.

    Returns: A tuple of
        - class_names: A list where class_names[i] is a list of strings giving the
          WordNet names for class i in the loaded dataset.
        - X_train: (N_tr, 3, 64, 64) array of training images
        - y_train: (N_tr,) array of training labels
        - X_val: (N_val, 3, 64, 64) array of validation images
        - y_val: (N_val,) array of validation labels
        - X_test: (N_test, 3, 64, 64) array of testing images.
        - y_test: (N_test,) array of test labels; if test labels are not available
          (such as in student code) then y_test will be None.
    """
    # First load wnids
    with open(os.path.join(path, 'wnids.txt'), 'r') as f:
        wnids = [x.strip() for x in f]

    # Map wnids to integer labels
    wnid_to_label = {wnid: i for i, wnid in enumerate(wnids)}

    # Use words.txt to get names for each class
    with open(os.path.join(path, 'words.txt'), 'r') as f:
        wnid_to_words = dict(line.split('\t') for line in f)
        for wnid, words in wnid_to_words.iteritems():
            wnid_to_words[wnid] = [w.strip() for w in words.split(',')]
    class_names = [wnid_to_words[wnid] for wnid in wnids]

    # Next load training data.
    X_train = []
    y_train = []
    for i, wnid in enumerate(wnids):
        if (i + 1) % 20 == 0:
            print('loading training data for synset %d / %d' % (i + 1,
                                                                len(wnids)))
        # To figure out the filenames we need to open the boxes file
        boxes_file = os.path.join(path, 'train', wnid, '%s_boxes.txt' % wnid)
        with open(boxes_file, 'r') as f:
            filenames = [x.split('\t')[0] for x in f]
        num_images = len(filenames)

        X_train_block = np.zeros((num_images, 3, 64, 64), dtype=dtype)
        y_train_block = wnid_to_label[wnid] * np.ones(num_images,
                                                      dtype=np.int64)
        for j, img_file in enumerate(filenames):
            img_file = os.path.join(path, 'train', wnid, 'images', img_file)
            img = imread(img_file)
            if img.ndim == 2:
                ## grayscale file
                img.shape = (64, 64, 1)
            X_train_block[j] = img.transpose(2, 0, 1)
        X_train.append(X_train_block)
        y_train.append(y_train_block)

        # We need to concatenate all training data
    X_train = np.concatenate(X_train, axis=0)
    y_train = np.concatenate(y_train, axis=0)

    # Next load validation data
    with open(os.path.join(path, 'val', 'val_annotations.txt'), 'r') as f:
        img_files = []
        val_wnids = []
        for line in f:
            img_file, wnid = line.split('\t')[:2]
            img_files.append(img_file)
            val_wnids.append(wnid)
        num_val = len(img_files)
        y_val = np.array([wnid_to_label[wnid] for wnid in val_wnids])
        X_val = np.zeros((num_val, 3, 64, 64), dtype=dtype)
        for i, img_file in enumerate(img_files):
            img_file = os.path.join(path, 'val', 'images', img_file)
            img = imread(img_file)
            if img.ndim == 2:
                img.shape = (64, 64, 1)
            X_val[i] = img.transpose(2, 0, 1)

    # Next load test images
    # Students won't have test labels, so we need to iterate over files in the
    # images directory.
    img_files = os.listdir(os.path.join(path, 'test', 'images'))
    X_test = np.zeros((len(img_files), 3, 64, 64), dtype=dtype)
    for i, img_file in enumerate(img_files):
        img_file = os.path.join(path, 'test', 'images', img_file)
        img = imread(img_file)
        if img.ndim == 2:
            img.shape = (64, 64, 1)
        X_test[i] = img.transpose(2, 0, 1)

    y_test = None
    y_test_file = os.path.join(path, 'test', 'test_annotations.txt')
    if os.path.isfile(y_test_file):
        with open(y_test_file, 'r') as f:
            img_file_to_wnid = {}
            for line in f:
                line = line.split('\t')
                img_file_to_wnid[line[0]] = line[1]
        y_test = [wnid_to_label[img_file_to_wnid[img_file]]
                  for img_file in img_files]
        y_test = np.array(y_test)

    return class_names, X_train, y_train, X_val, y_val, X_test, y_test


def adding_problem_generator(N, seq_len=30, high=1):
    """ A data generator for adding problem.

    The data definition strictly follows Quoc V. Le, Navdeep Jaitly, Geoffrey E.
    Hintan's paper, A Simple Way to Initialize Recurrent Networks of Rectified
    Linear Units.

    The single datum entry is a 2D vector with two rows with same length.
    The first row is a list of random data; the second row is a list of binary
    mask with all ones, except two positions sampled by uniform distribution.
    The corresponding label entry is the sum of the masked data. For
    example:
    
     input          label
     -----          -----
    1 4 5 3  ----->   9 (4 + 5)
    0 1 1 0

    :param N: the number of the entries.
    :param seq_len: the length of a single sequence.
    :param p: the probability of 1 in generated mask
    :param high: the random data is sampled from a [0, high] uniform distribution.
    :return: (X, Y), X the data, Y the label.
    """
    X_num = np.random.uniform(low=0, high=high, size=(N, seq_len, 1))
    X_mask = np.zeros((N, seq_len, 1))
    Y = np.ones((N, 1))
    for i in xrange(N):
        # Default uniform distribution on position sampling
        positions = np.random.choice(seq_len, size=2, replace=False)
        X_mask[i, positions] = 1
        Y[i, 0] = np.sum(X_num[i, positions])
    X = np.append(X_num, X_mask, axis=2)
    return X, Y


def gaussian_cluster_generator(num_samples=10000, num_features=500, num_classes=5):
    """ Generates several clusters of Gaussian points """
    mu = np.random.rand(num_classes, num_features)
    sigma = np.ones((num_classes, num_features)) * 0.1
    num_cls_samples = num_samples / num_classes
    x = np.zeros((num_samples, num_features))
    y = np.zeros((num_samples, num_classes))
    for i in range(num_classes):
        cls_samples = np.random.normal(mu[i,:], sigma[i,:], (num_cls_samples, num_features))
        x[i*num_cls_samples:(i+1)*num_cls_samples] = cls_samples
        y[i*num_cls_samples:(i+1)*num_cls_samples,i] = 1
    return x, y


def load_models(models_dir):
    """Load saved models from disk. This will attempt to unpickle all files in a
    directory; any files that give errors on unpickling (such as README.txt) will
    be skipped.

    Inputs:
        - models_dir: String giving the path to a directory containing model files.
          Each model file is a pickled dictionary with a 'model' field.

    Returns:
        A dictionary mapping model file names to models.
    """
    models = {}
    for model_file in os.listdir(models_dir):
        with open(os.path.join(models_dir, model_file), 'rb') as f:
            try:
                models[model_file] = pickle.load(f, encoding='latin1')['model']
            except pickle.UnpicklingError:
                continue
    return models


def get_MNIST_data(**kwargs):
    """Load MNIST data.

    Inputs:
        - batch_size:
        - data_dir:
        - normalize:
        - shape:

    Returns:
        - training: mxnet.io.NDArrayIter
        - test: mxnet.io.NDArrayIter
    """
    from joblib import load
    data = load(kwargs['data_dir'] + 'mnist.dat')

    if kwargs.get('normalize', True):
        epsilon = 1e-5
        mean = np.mean(data['train_data'], axis=0)
        std = np.std(data['train_data'], axis=0)
        for key, value in data.items():
            if 'data' in key: data[key] = (value - mean) / (std + epsilon)

    if 'shape' in kwargs:
        for key, value in data.items():
            if 'data' in key:
                data[key] = value.reshape((len(value),) + kwargs['shape'])

    from mxnet.io import NDArrayIter
    batch_size = kwargs['batch_size']
    training = NDArrayIter(data['train_data'], data['train_label'], batch_size, shuffle=True)
    test = NDArrayIter(data['test_data'], data['test_label'], batch_size, shuffle=False)

    return training, test


def get_imagenet_data(batch_size=None, path=None):
    """Load Imagenet data.

    Inputs:
        - batch_size:
        - data_dir:

    Returns:
        - training: mxnet.io.ImageRecordIter
        - test: mxnet.io.ImageRecordIter
    """
    path = '%sILSVRC2012_img_val.tar' % path

    r_mean = 123.680
    g_mean = 116.779
    b_mean = 103.939
    mean = int((r_mean + g_mean + b_mean) / 3)
    scale = 1 / 59.4415

    from mxnet.io import ImageRecordIter

    training = ImageRecordIter(
        batch_size         = batch_size,
        data_name          = 'data',
        data_shape         = (3, 224, 224),
        fill_value         = mean,
        label_name         = 'softmax_label',
        mean_r             = r_mean,
        mean_g             = g_mean,
        mean_b             = b_mean,
        num_parts          = 2,
        pad                = 4,
        path_imgrec        = path,
        part_index         = 0,
        preprocess_threads = 16,
        rand_crop          = True,
        rand_mirror        = True,
        scale              = scale,
        shuffle            = True,
        verbose            = False,
    )

    test = ImageRecordIter(
        batch_size         = batch_size,
        data_name          = 'data',
        data_shape         = (3, 224, 224),
        label_name         = 'softmax_label',
        mean_r             = r_mean,
        mean_g             = g_mean,
        mean_b             = b_mean,
        num_parts          = 2,
        part_index         = 1,
        path_imgrec        = path,
        preprocess_threads = 16,
        scale              = scale,
        verbose            = False,
    )

    return training, test


def fetch_and_get_mnist():
    mnist = fetch_mldata('MNIST original')
    np.random.seed(1234) # set seed for deterministic ordering
    p = np.random.permutation(mnist.data.shape[0])
    X = mnist.data[p]  
    X = X.reshape((70000, 28, 28))
    X = np.asarray([cv2.resize(x, (64,64)) for x in X])
    X = X.astype(np.float32)/(255.0/2) - 1.0
    X = X.reshape((70000, 1, 64, 64))
    X = np.tile(X, (1, 3, 1, 1))
    X_train = X[:60000]
    X_test = X[60000:]
    return X_train, X_test
