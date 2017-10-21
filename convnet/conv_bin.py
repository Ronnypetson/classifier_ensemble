from __future__ import print_function
import tensorflow as tf
import cv2
import numpy as np
import os, random

img_dir = '../../converted/segmented/cropped/'
trem_dir = 'TREMULOUS/'
thorpe_dir = 'Thorpe/'
img_dim = 20
batch_size = 16
learning_rate = 0.001
num_steps = 1000
num_epochs = 5
dropout = 0.75
classes = {0:'a/',1:'e/',2:'o/',3:'u/'}

def get_batch():    # X: (batch_size,28,28), Y: (batch_size,2)
    trem_size = batch_size/2
    thorpe_size = batch_size-trem_size
    X = []
    Y = []
    for i in range(trem_size):  # trem: [1,0], thorpe: [0,1]
        fl_loc = img_dir+trem_dir+classes[i%len(classes)]
        fl = random.choice(os.listdir(fl_loc))
        #print(fl_loc+fl)
        img = cv2.imread(fl_loc+fl,0)
        img = cv2.resize(img,(img_dim,img_dim))
        X.append(img)
        Y.append([1.0,0.0])
    for i in range(thorpe_size):
        fl_loc = img_dir+thorpe_dir+classes[i%len(classes)]
        fl = random.choice(os.listdir(fl_loc))
        #print(fl_loc+fl)
        img = cv2.imread(fl_loc+fl,0)
        img = cv2.resize(img,(img_dim,img_dim))
        X.append(img)
        Y.append([0.0,1.0])
    return X,Y

def bin1(X):
    X = tf.reshape(X,shape=[-1,img_dim,img_dim,1])    #
    # conv, conv, fc, fc
    c1 = tf.layers.conv2d(X,32,5,activation=tf.nn.relu)
    c1 = tf.layers.max_pooling2d(c1,2,2)
    #
    c2 = tf.layers.conv2d(c1,64,3,activation=tf.nn.relu)
    c2 = tf.layers.max_pooling2d(c2,2,2)
    #
    fc = tf.contrib.layers.flatten(c2)
    fc = tf.layers.dense(fc,200)
    fc = tf.layers.dropout(fc,rate=dropout)
    return tf.layers.dense(fc,2)

X = tf.placeholder(tf.float32,shape=(None,img_dim,img_dim))
Y = tf.placeholder(tf.float32,shape=(None,2))

loss = tf.reduce_mean(tf.losses.softmax_cross_entropy(Y,bin1(X)))
train = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss)
eq = tf.equal(tf.argmax(bin1(X),1),tf.argmax(Y,1))
acc = tf.reduce_mean(tf.cast(eq,tf.float32))
#acc = tf.metrics.accuracy(labels=tf.argmax(Y,axis=0),predictions=tf.argmax(bin1(X),axis=0))

with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    s_loss = 0.0
    s_acc = 0.0
    for j in range(num_epochs):
        print('Epoch '+str(j))
        for i in range(num_steps):
            x_,y_ = get_batch()
            _,loss_,acc_,eq_ = sess.run([train,loss,acc,eq],feed_dict={X:x_,Y:y_})
            s_loss += loss_
            s_acc += acc_
            #acc_ = sess.run(acc,feed_dict={X:x_,Y:y_})
            if i%100 == 0:
                print('loss: ',s_loss/100,'accuracy: ',s_acc/100)
                print(eq_)
                s_loss = 0.0
                s_acc = 0.0
