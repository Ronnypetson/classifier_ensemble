from __future__ import print_function
import tensorflow as tf
import cv2
import numpy as np
import os, random

###
train_dir = 'TREMULOUS/'
test_dir = 'test/'+train_dir
num_steps = 1000
num_epochs = 5
batch_size = 64
cl_type = 'fc'
#
model_ckpt = '/checkpoint/conv_vowel/'
model_fn = model_ckpt+train_dir+cl_type+'_'+str(batch_size)+'_'+str(num_epochs*num_steps)+'_model.ckpt'
img_dir = '../../converted/segmented/cropped/'  #'augmented/'
#
img_dim = 20
learning_rate = 0.001
dropout = 0.75
classes = ['a/','e/','o/','u/'] #['a/','e/','o/','u/']
num_classes = len(classes) # a e o u
###

def get_test(test_directory=test_dir):
    X = []
    Y = []
    for i in range(num_classes):
        fl_loc = img_dir+test_directory+classes[i]
        fls = os.listdir(fl_loc)
        for fl in fls:
            img = cv2.imread(fl_loc+fl,0)
            img = img/255.0
            X.append(img)
            y_ = np.zeros((num_classes),np.float32)
            y_[i] = 1.0
            Y.append(y_)
    return X,Y

def get_batch():    # X: (batch_size,28,28), Y: (batch_size,4)
    X = []
    Y = []
    for i in range(batch_size):  # one-hot encoding
        class_ = random.randint(0,num_classes-1)
        fl_loc = img_dir+train_dir+classes[class_]
        fl = random.choice(os.listdir(fl_loc))
        #print(class_,fl)
        #print(fl_loc+fl)
        img = cv2.imread(fl_loc+fl,0)
        img = img/255.0
        #img = cv2.resize(img,(img_dim,img_dim)) #
        #_,img = cv2.threshold(img,127,255,cv2.THRESH_BINARY)  #
        #img = cv2.medianBlur(img,3) #
        X.append(img)
        y_ = np.zeros((num_classes),np.float32)  #[0.0,0.0,0.0,0.0]
        y_[class_] = 1.0
        Y.append(y_)
    return X,Y

def vowel_fc(X):
      # Create the model
      x = tf.reshape(X,shape=[-1,400])
      W = tf.Variable(tf.zeros([400, num_classes]))
      b = tf.Variable(tf.zeros([num_classes]))
      y = tf.matmul(x, W) + b
      return tf.nn.softmax(y,name="out_")

def vowel_cl(X):
    X_ = tf.reshape(X,shape=[-1,img_dim,img_dim,1])    #
    # conv, conv, fc, fc
    c1 = tf.layers.conv2d(X_,32,5,activation=tf.nn.relu) # 32
    c1 = tf.layers.max_pooling2d(c1,2,2)
    #
    c2 = tf.layers.conv2d(c1,64,3,activation=tf.nn.relu)    # 64
    c2 = tf.layers.max_pooling2d(c2,2,2)
    #
    fc = tf.contrib.layers.flatten(c2)
    fc = tf.layers.dense(fc,200,activation=tf.nn.relu)    # 200
    #fc = tf.layers.dropout(fc,rate=dropout)
    fc2 = tf.layers.dense(fc,num_classes,activation=None)
    return tf.nn.softmax(fc2,name="out_")

X = tf.placeholder(tf.float32,shape=(None,img_dim,img_dim),name="X") # 
Y = tf.placeholder(tf.float32,shape=(None,num_classes),name="Y") # 

#loss = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=tf.argmax(Y,1),logits=vowel_cl(X))
#loss = tf.losses.softmax_cross_entropy(onehot_labels=Y,logits=vowel_cl(X))
if cl_type == 'cl':
    output_ = vowel_cl(X)
elif cl_type == 'fc':
    output_ = vowel_fc(X)

loss = tf.losses.mean_squared_error(Y,output_)
eq = tf.equal(tf.argmax(output_,1),tf.argmax(Y,1))
acc = tf.reduce_mean(tf.cast(eq,tf.float32),name="accuracy")
train = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(loss)
confusion = tf.confusion_matrix(labels=tf.argmax(Y,1),predictions=tf.argmax(output_,1))   # ,num_classes=num_classes

with tf.Session() as sess:
    saver = tf.train.Saver()
    if os.path.isfile(model_fn+'.meta'):
        saver.restore(sess,model_fn)
    else:
        sess.run(tf.global_variables_initializer())
    #
    s_loss = 0.0
    t_x,t_y = get_test()    # test batch for evaluating accuracy
    #
    for j in range(num_epochs):
        print('Epoch '+str(j))
        for i in range(num_steps):
            x_,y_ = get_batch()
            _,loss_ = sess.run([train,loss],feed_dict={X:x_,Y:y_})
            s_loss += loss_
            if i%100 == 99:
                # test
                conf, acc_ = sess.run([confusion,acc],feed_dict={X:t_x,Y:t_y})
                print('loss: ',s_loss/100,'accuracy: ',acc_)
                conf = [r*1.0/sum(r) for r in conf]
                conf = [r.tolist() for r in conf]
                print(conf)
                s_loss = 0.0
                if i%1000 == 999:
                    saver.save(sess,model_fn)

